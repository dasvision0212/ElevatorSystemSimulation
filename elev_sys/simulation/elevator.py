from elev_sys.simulation import floor
import simpy
import random
import numpy as np
from copy import deepcopy
import logging

from elev_sys.conf.elevator_conf import ELEV_CONFIG
from elev_sys.conf.log_conf import ELEVLOG_CONFIG
from elev_sys.simulation.simple_data_structure import Mission
from elev_sys.simulation.event import Event
from elev_sys.simulation.logger import Elev_logger, Customer_logger, StopList_logger
from elev_sys.animation.general import cal_floorNum
from elev_sys.simulation.utils import cal_displacement, advance, floor_complement


class IndexError(Exception):
    """Exception : Wrong Index."""
    pass

class StopList:
    IDLE = 0
    ACTIVE = 1
    NA = -1

    def __init__(self, floorList, available_floor, stopList_logger:StopList_logger=None):
        # self.floorList = deepcopy(floorList)
        self.stopList_logger = stopList_logger

        self._list = {
             1: [0] * (len(floorList)),
            -1: [0] * (len(floorList))
        }

        # dictionary for indexing
        self.index = {
            1: {floor: index for index, floor in enumerate(floorList)},
            -1: {floor: index for index, floor in enumerate(reversed(floorList))}
        }

        infeasible_floor = floor_complement(floorList, available_floor)
        for floorName in infeasible_floor:
            self._list[1][self.index[1][floorName]] = StopList.NA
            self._list[-1][self.index[-1][floorName]] = StopList.NA

        self.reversed_index = {
            1: {index: floor for index, floor in enumerate(floorList)},
            -1: {index: floor for index, floor in enumerate(reversed(floorList))}
        }

    def notEmpyty(self):
        notEmpty = False
        for i, j in zip(self._list[1], self._list[-1]):
            if i == StopList.ACTIVE or j == StopList.ACTIVE:
                notEmpty = True
        return notEmpty

    def pushOuter(self, elev, direction, floor):
        currentIndex = self.index[direction][floor]

        # illegal index
        if self._list[direction][currentIndex] == StopList.NA:
            raise IndexError()

        # add outer call to stoplist
        self._list[direction][currentIndex] = StopList.ACTIVE
        if(not self.stopList_logger is None):
            self.stopList_logger.log_active(elev.elev_name, direction, currentIndex, float(elev.env.now))

    def pushInner(self, elev, destination):
        floorIndex = self.index[elev.direction][destination]

        # illegal index
        if self._list[elev.direction][floorIndex] == StopList.NA:
            raise IndexError()

        # add inner call to stoplist
        self._list[elev.direction][floorIndex] = StopList.ACTIVE
        if(not self.stopList_logger is None):
            self.stopList_logger.log_active(elev.elev_name, elev.direction, floorIndex, float(elev.env.now))


    def pop(self, elev):
        currentIndex = self.index[elev.direction][elev.current_floor]

        # illegal index
        if self._list[elev.direction][currentIndex] == StopList.NA:
            raise IndexError()

        # remove target floor from stoplist
        self._list[elev.direction][currentIndex] = StopList.IDLE
        if(not self.stopList_logger is None):
            self.stopList_logger.log_idle(elev.elev_name, elev.direction, currentIndex, float(elev.env.now))
            
        logging.debug('[POP] ele {}, curFlo {}, dir {}'.format(
            elev.elev_name, elev.current_floor, elev.direction))

    def next_target(self, elev):
        current_floor = elev.current_floor

        if ELEV_CONFIG.VERSION == 2:
            peak = None

            # same direction, front
            curr_index = self.index[elev.direction][current_floor]
            for i, state in enumerate(self._list[elev.direction][curr_index:]):
                if state == StopList.ACTIVE:
                    return self.reversed_index[elev.direction][i+curr_index]

                # compute ligetimate peak
                if state != StopList.NA:
                    peak = self.reversed_index[elev.direction][i+curr_index]

            # different direction
            for i, state in enumerate(self._list[-elev.direction]):
                if state == StopList.ACTIVE:
                    return peak

            # same direction, back
            for i, state in enumerate(self._list[elev.direction][:curr_index]):
                if state == StopList.ACTIVE:
                    return self.reversed_index[elev.direction][i]
        elif isinstance(ELEV_CONFIG.VERSION, int):
            # same direction, front
            curr_index = self.index[elev.direction][current_floor]
            for i, state in enumerate(self._list[elev.direction][curr_index:]):
                if state == StopList.ACTIVE:
                    return self.reversed_index[elev.direction][i+curr_index]

            # different direction
            for i, state in enumerate(self._list[-elev.direction]):
                if state == StopList.ACTIVE:
                    return self.reversed_index[-elev.direction][i]

            # same direction, back
            for i, state in enumerate(self._list[elev.direction][:curr_index]):
                if state == StopList.ACTIVE:
                    return self.reversed_index[elev.direction][i]
        else:
            raise Exception("[! The version of elevator simulation system is not supported. ")

        return None

    def isNA(self, direction, floor):
        if(self._list[direction][self.index[direction][floor]] == StopList.NA):
            return True
        else:
            return False

    def floor_rank(self, elev, direction, destination):

        curr_index = self.index[elev.direction][elev.current_floor]
        # same direction, front
        if(direction == elev.direction):
            floor_diff = cal_displacement(elev.current, destination)
            if(floor_diff * direction > 0):
                return floor_diff
        
        # diffrent direction        
        change_point_index = curr_index
        for i, state in enumerate(self._list[elev.direction][curr_index:]):
            if state == StopList.ACTIVE:
                change_point_index += 1

        if(direction != elev.direction):
            return cal_displacement(elev.current, self.reversed_index[elev.direction][change_point_index]) * elev.direction + \
                   abs(cal_displacement(self.reversed_index[elev.direction][change_point_index], destination))

        # same direction, back
        for i, state in enumerate(self._list[-elev.direction][:curr_index]):
            if state == StopList.ACTIVE:
                return self.reversed_index[elev.direction][i]


class Elevator:
    def __init__(self, env, elev_name, floorList, available_floor, EVENT: Event,
                 customer_logger: Customer_logger=None, elev_logger: Elev_logger=None, stopList_logger:StopList_logger=None):
        self.env = env
        self.elev_name = str(elev_name)
        self.capacity = ELEV_CONFIG.ELEV_CAPACITY
        self.riders = []
        self.EVENT = EVENT
        self.floorList = floorList
        self.available_floor = available_floor

        # schedule list
        self.stop_list = StopList(floorList, available_floor, stopList_logger)

        # initial states
        self.current_floor = available_floor[0]
        

        self.direction = 0
        self.ASSIGN_EVENT = self.env.event()
        self.FINISH_EVENT = self.env.event()
        # start process
        self.env.process(self.idle())

        # logger
        self.customer_logger = customer_logger
        self.elev_logger = elev_logger

        # statistic
        self.stopNum   = 0 # the number that the elevator stop at any floor
        self.wasteStopNum = 0
        self.moveFloorNum = 0

    #     self.env.process(self.debug())
    # def debug(self):
    #     if (self.elev_name == 'a1'):
    #         while True:
    #             yield self.env.timeout(10)
    #             if self.current_floor == '5':
    #                 print(self.elev_name,self.direction, self.current_floor,'down',self.stop_list._list[-1][10:-4])


    def idle(self):
        logging.info('[IDLE] Elev {} Activated'.format(self.elev_name))

        while True:
            if(not self.elev_logger is None):
                self.elev_logger.log_idle(self.elev_name, self.current_floor, float(self.env.now))

            # first assignment
            mission = yield self.ASSIGN_EVENT
            # reactivate
            self.ASSIGN_EVENT = self.env.event()
            self.FINISH_EVENT.succeed()
            self.FINISH_EVENT = self.env.event()

            logging.debug('[Assign_event - idle] Elev {}, stopList {}'.format(self.elev_name, self.stop_list))
            logging.info('[IDLE] Elev {}, Outer Call: {}'.format(self.elev_name, mission))

            # push outer call
            self.stop_list.pushOuter(self, mission.direction, mission.destination)

            # determine initial direction
            displacement = cal_displacement(self.current_floor, mission.destination)
            if displacement > 0:
                self.direction = 1
            elif displacement < 0:
                self.direction = -1
            else:
                # same floor, forced direction
                self.direction = mission.direction

            yield self.env.process(self.onMission())
            
            # return to IDLE state
            self.direction = 0
            logging.info('[IDLE] Elev {} Stopped.'.format(self.elev_name))

    def onMission(self):
        while self.stop_list.notEmpyty():

            # initialize moving process
            nextTarget = self.stop_list.next_target(self)
            moving_proc = self.env.process(self.moving(nextTarget, self.current_floor))

            logging.info('[ONMISSION] Elev {}, NEXT TARGET {}'.format(self.elev_name, nextTarget))
            
            # before arriving target destination
            while not self.current_floor == nextTarget:

                value = yield self.ASSIGN_EVENT | moving_proc

                if self.ASSIGN_EVENT.triggered:
                    mission = list(value.values())[0]
                    self.ASSIGN_EVENT = self.env.event()
                    self.FINISH_EVENT.succeed()
                    self.FINISH_EVENT = self.env.event()
                    
                    logging.info('[ONMISSION] Elev {}, New OuterCall {}'.format(
                        self.elev_name, mission))

                    # previous next Target
                    temp = nextTarget

                    self.stop_list.pushOuter(self, mission.direction, mission.destination)
                    nextTarget = self.stop_list.next_target(self)
                    
                    logging.debug('[ONMISSION] Elev {}, STOP LIST {}'.format(self.elev_name, self.stop_list))
                    logging.info('[ONMISSION] Elev {}, NEXT TARGET {}'.format(self.elev_name, nextTarget))

                    # target changed, interrupt current mission
                    if temp != nextTarget:
                        moving_proc.interrupt()
                        moving_proc = self.env.process(self.moving(nextTarget, self.current_floor))

            logging.info('[ONMISSION] Elev {}, Arrive At {} Floor'.format(self.elev_name, self.current_floor))

            # arrive taarget floor
            yield self.env.process(self.serving())

            logging.info('[Afer Serving] Elev {}, rider {}'.format(self.elev_name, [(vars(i)) for i in self.riders]))

    def moving(self, destination, source):
        """source is needed to account for the acceleration and deceleration rate of the elevator"""
        
        logging.info('[MOVING] Elev {}, Moving Process Started: to {}'.format(self.elev_name, destination))

        try:
            while self.current_floor != destination:

                # calculate traveling time for passing 1 floor
                yield self.env.timeout(ELEV_CONFIG.ELEV_VELOCITY)

                # advance 1 floor
                self.current_floor = advance(self.current_floor, self.direction)
                self.moveFloorNum += 1

                if(not self.elev_logger is None):
                    self.elev_logger.log_arrive(self.elev_name, self.direction, self.current_floor, float(self.env.now))
                logging.info('[MOVING] Elev {}, Update To {} Floor'.format(self.elev_name, self.current_floor))

        except simpy.Interrupt:
            logging.info('[MOVING] Elev {}, Interrupted'.format(self.elev_name))
            logging.debug('[MOVING] Elev {}, stop_list {}'.format(self.elev_name, self.stop_list))

    def serving(self):
        isWasted = True

        # Count Elevator Stop
        self.stopNum += 1

        # Door Opens
        yield self.env.timeout(ELEV_CONFIG.ELEV_OPEN)

        # Cross out current target
        self.stop_list.pop(self)

        logging.info('[SERVING] Elev {}, after pop:{}'.format(self.elev_name, self.stop_list))

        # 
        fulfill_customer = []
        transfer_customers= []
        for i in range(len(self.riders)-1, -1, -1):
            # customer arrive destination
            if(self.riders[i].destination ==  self.current_floor):

                customer = self.riders.pop(i)
                fulfill_customer.append(customer)

                if(not self.customer_logger is None):
                    self.customer_logger.log_get_off(customer.cid, self.current_floor, float(self.env.now))
            
            # customer wait to transfer
            elif(self.riders[i].temp_destination ==  self.current_floor):
                customer = self.riders.pop(i)
                transfer_customers.append(customer)

                if(not self.customer_logger is None):
                    self.customer_logger.log_get_off(customer.cid, self.current_floor, float(self.env.now))

                
        leaveNum = len(fulfill_customer) + len(transfer_customers)  

        if leaveNum > 0:
            isWasted = False

        total_walking_time = [np.random.randint(ELEV_CONFIG.WALKING_MIN, ELEV_CONFIG.WALKING_MAX) for i in range(leaveNum)]
        yield self.env.timeout(sum(total_walking_time))

        logging.info('[SERVING] Elev {}, {} Customers Leave'.format(self.elev_name, leaveNum))

        # transfer customer enter queue
        if transfer_customers:
            self.EVENT.ELEV_TRANSFER[self.direction][self.current_floor].succeed(value=transfer_customers)
            self.EVENT.ELEV_TRANSFER[self.direction][self.current_floor] = self.env.event()

        # The common situation, not on the peak
        if not ((self.current_floor == self.available_floor[-1] and self.direction == 1) or \
               (self.current_floor == self.available_floor[0] and self.direction == -1)):
            
            # elevator signal queue
            self.EVENT.ELEV_ARRIVAL[self.direction][self.current_floor].succeed(value=(self.capacity-len(self.riders), self.elev_name))
            self.EVENT.ELEV_ARRIVAL[self.direction][self.current_floor] = self.env.event()
            
            # customers on board
            riders = yield self.EVENT.ELEV_LEAVE[self.elev_name]

            if len(riders) > 0:
                isWasted = False

            logging.info('[SERVING] Elev {}, Customers Aboard: \n {}'.format(self.elev_name, [vars(i) for i in riders]))

            # add inner calls
            for customer in riders:
                destination = customer.next_stop(self.current_floor)
                self.stop_list.pushInner(self, destination)

            self.riders = self.riders + riders

            if(not self.elev_logger is None):
                self.elev_logger.log_serve(self.elev_name, len(self.riders), self.direction, self.current_floor, float(self.env.now))

        # Update Target
        nextTarget = self.stop_list.next_target(self)

        logging.info('[SERVING] Elev {}, NEXT TARGET {}'.format(self.elev_name, nextTarget))

        # if no target, turn idle
        if nextTarget == None:
            logging.debug('[SERVING] Elev {}, nextTarget is None, {}'.format(self.elev_name, nextTarget))
            return
        
        # update direction
        else:
            logging.debug('[SERVING] Elev {}, currFloor {}, nextTarget {}'.format(
                self.elev_name, self.current_floor, nextTarget))

            displacement = cal_displacement(self.current_floor, nextTarget)
            if displacement > 0:
                self.direction = 1
            elif displacement < 0:
                self.direction = -1
            
            # same target floor means change direction
            else:
                # make a turn
                self.direction = -1*self.direction
                self.stop_list.pop(self)

                # customers on board
                
                self.EVENT.ELEV_ARRIVAL[self.direction][self.current_floor].succeed(value=(self.capacity-len(self.riders), self.elev_name))
                self.EVENT.ELEV_ARRIVAL[self.direction][self.current_floor] = self.env.event()

                # new customers
                riders = yield self.EVENT.ELEV_LEAVE[self.elev_name]

                if len(riders) > 0:
                    isWasted = False

                logging.info('[SERVING] Elev {}, Customers Aboard: \n {} '.format(self.elev_name, [vars(i) for i in riders]))

                for customer in riders:
                    temp_destination = customer.next_stop(self.current_floor)
                    self.stop_list.pushInner(self, temp_destination)
                
                self.riders = self.riders + riders

                if(not self.elev_logger is None):
                    self.elev_logger.log_serve(
                        self.elev_name, len(self.riders), self.direction, self.current_floor, float(self.env.now))

        # Update Wasted Stop
        if isWasted:
            self.wasteStopNum += 1
        
        # Door Close
        yield self.env.timeout(ELEV_CONFIG.ELEV_CLOSE)