import simpy
import random
from copy import deepcopy
import logging

from elev_sys.conf.NTUH_conf import ELEV_INFEASIBLE
from elev_sys.conf.elevator_conf import ELEV_CONFIG
from elev_sys.conf.log_conf import ELEVLOG_CONFIG
from elev_sys.simulation.simple_data_structure import Mission
from elev_sys.simulation.event import Event
from elev_sys.simulation.logger import Elev_logger, Customer_logger, StopList_logger
from elev_sys.animation.general import cal_floorNum


def displacement(floor1, floor2):
    floor1 = int(floor1) if not 'B' in floor1 else -int(floor1[1:]) + 1
    floor2 = int(floor2) if not 'B' in floor2 else -int(floor2[1:]) + 1
    return floor2-floor1


class IndexError(Exception):
    """Exception : Wrong Index."""
    pass


class StopList:
    IDLE = 0
    ACTIVE = 1
    NA = -1

    def __init__(self, FloorList, infeasible, stopList_logger:StopList_logger=None):
        self.floorList = deepcopy(FloorList)
        self.stopList_logger = stopList_logger

        self._list = {
             1: [0] * (len(FloorList)),
            -1: [0] * (len(FloorList))
        }

        # dictionary for indexing
        self.index = {
            1: {floor: index for index, floor in enumerate(FloorList)},
            -1: {floor: index for index, floor in enumerate(reversed(FloorList))}
        }

        for floorName in infeasible:
            self._list[1][self.index[1][floorName]] = StopList.NA
            self._list[-1][self.index[-1][floorName]] = StopList.NA

        self.reversed_index = {
            1: {index: floor for index, floor in enumerate(FloorList)},
            -1: {index: floor for index, floor in enumerate(reversed(FloorList))}
        }

    def __str__(self):
        string = 'Stop List: \n  up   down \n'
        formatStr = ['{} [{}] [{}] {}\n'.format(f, i, j, f) for f, i, j in zip(self.floorList, self._list[1], self._list[-1])]
        string.join(formatStr)
        return str(formatStr)
#     up  down
# 4   [0]  [0]
# 3   [1]  [1]
# 2   [0]  [0]
# 1   [1]  [0]

    def isEmpyty(self):
        for i, j in zip(self._list[1], self._list[-1]):
            if i == StopList.ACTIVE or j == StopList.ACTIVE:
                return False
        return True

    def pushOuter(self, elev, direction, floor):
        currentIndex = self.index[direction][floor]

        # illegal index
        if self._list[direction][currentIndex] == StopList.NA:
            raise IndexError()

        # add outer call to stoplist
        self._list[direction][currentIndex] = StopList.ACTIVE
        if(self.stopList_logger != None):
            self.stopList_logger.log_active(elev.elev_name, direction, currentIndex, float(elev.env.now))

    def pushInner(self, elev, destination):
        floorIndex = self.index[elev.direction][destination]

        # illegal index
        if self._list[elev.direction][floorIndex] == StopList.NA:
            raise IndexError()

        # add inner call to stoplist
        self._list[elev.direction][floorIndex] = StopList.ACTIVE
        if(self.stopList_logger != None):
            self.stopList_logger.log_active(elev.elev_name, elev.direction, floorIndex, float(elev.env.now))


    def pop(self, elev):
        currentIndex = self.index[elev.direction][elev.current_floor]

        # illegal index
        if self._list[elev.direction][currentIndex] == StopList.NA:
            raise IndexError()

        # remove target floor from stoplist
        self._list[elev.direction][currentIndex] = StopList.IDLE
        if(self.stopList_logger != None):
            self.stopList_logger.log_idle(elev.elev_name, elev.direction, currentIndex, float(elev.env.now))
            
        logging.debug('[POP] ele {}, curFlo {}, dir {}'.format(
            elev.elev_name, elev.current_floor, elev.direction))

    def next_target(self, elev):
        current_floor = elev.current_floor

        if ELEV_CONFIG.VERSION == 3:
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
            floor_diff = displacement(elev.current, destination)
            if(floor_diff * direction > 0):
                return floor_diff
        
        # diffrent direction        
        change_point_index = curr_index
        for i, state in enumerate(self._list[elev.direction][curr_index:]):
            if state == StopList.ACTIVE:
                change_point_index += 1

        if(direction != elev.direction):
            return displacement(elev.current, self.reversed_index[elev.direction][change_point_index]) * elev.direction + \
                   abs(displacement(self.reversed_index[elev.direction][change_point_index], destination))

        # same direction, back
        for i, state in enumerate(self._list[-elev.direction][:curr_index]):
            if state == StopList.ACTIVE:
                return self.reversed_index[elev.direction][i]


class Elevator:
    def __init__(self, env, elev_name, floorList, infeasible, EVENT: Event,
                 customer_logger: Customer_logger=None, elev_logger: Elev_logger=None, stopList_logger:StopList_logger=None):
        self.env = env
        self.elev_name = str(elev_name)
        self.capacity = ELEV_CONFIG.ELEV_CAPACITY
        self.riders = []
        self.EVENT = EVENT
        self.floorList = floorList

        # schedule list
        # print('!!!!!!!!!!!!',elev_name, infeasible)
        self.stop_list = StopList(self.floorList, infeasible, stopList_logger)
        self.infeasible = infeasible

        # initial states
        self.current_floor = '1'
        self.direction = 0
        self.assign_event = self.env.event()
        self.finish_event = self.env.event()
        # start process
        self.env.process(self.idle())

        # logger
        self.customer_logger = customer_logger
        self.elev_logger = elev_logger

        # statistic
        self.stopNum   = 0 # the number that the elevator stop at any floor
        self.wasteStopNum = 0
        self.moveFloorNum = 0

    def idle(self):
        logging.info('[IDLE] Elev {} Activated'.format(self.elev_name))
#         print('[IDLE] Elevator {} Activated'.format(self.elev_name))

        while True:
            if(self.elev_logger != None):
                self.elev_logger.log_idle(self.elev_name, self.current_floor, float(self.env.now))

            # first assignment
            mission = yield self.assign_event
            logging.debug(
                '[Assign_event - idle] Elev {}, stopList {}'.format(self.elev_name, self.stop_list))

            # reactivate
            self.assign_event = self.env.event()
            self.finish_event.succeed()
            self.finish_event = self.env.event()

            logging.info('[IDLE] Elev {}, Outer Call: {}'.format(
                self.elev_name, mission))

            # push outer call
            self.stop_list.pushOuter(self, mission.direction, mission.destination)

            # determine initial direction
            if displacement(self.current_floor, mission.destination) > 0:
                self.direction = 1
            elif displacement(self.current_floor, mission.destination) < 0:
                self.direction = -1
            else:
                # set the direction of elevator to that of mission
                self.direction = mission.direction

            # start onMission process
            yield self.env.process(self.onMission())
            logging.info('[IDLE] Elev {} Stopped.'.format(self.elev_name))

            # return to IDLE state
            self.direction = 0

    def onMission(self):
        while not self.stop_list.isEmpyty():

            nextTarget = self.stop_list.next_target(self)
#             logging.info('[ONMISSION] NEXT TARGET {}'.format(nextTarget))
            logging.info('[ONMISSION] Elev {}, NEXT TARGET {}'.format(
                self.elev_name, nextTarget))
#             print('[ONMISSION] NEXT TARGET {}'.format(nextTarget))

            moving_proc = self.env.process(
                self.moving(nextTarget, self.current_floor))

            while self.current_floor != nextTarget:
                value = yield self.assign_event | moving_proc
                if self.assign_event.triggered:

                    mission = value[self.assign_event]
                    self.assign_event = self.env.event()
                    self.finish_event.succeed()
                    self.finish_event = self.env.event()
                    logging.info('[ONMISSION] Elev {}, New OuterCall {}'.format(
                        self.elev_name, mission))

                    before = nextTarget

                    self.stop_list.pushOuter(
                        self, mission.direction, mission.destination)
                    logging.debug('[ONMISSION] Elev {}, STOP LIST {}'.format(
                        self.elev_name, self.stop_list))

                    nextTarget = self.stop_list.next_target(self)
                    logging.info('[ONMISSION] Elev {}, NEXT TARGET {}'.format(
                        self.elev_name, nextTarget))

                    if before != nextTarget:
                        moving_proc.interrupt()
                        moving_proc = self.env.process(
                            self.moving(nextTarget, self.current_floor))

            logging.info('[ONMISSION] Elev {}, Arrive At {} Floor'.format(
                self.elev_name, self.current_floor))
            yield self.env.process(self.serving())
            logging.info('[Afer Serving] Elev {}, rider {}'.format(
                self.elev_name, [(vars(i)) for i in self.riders]))

    def moving(self, destination, source):
        """source is needed to account for the acceleration and deceleration rate of the elevator"""
        logging.info('[MOVING] Elev {}, Moving Process Started: to {}'.format(
            self.elev_name, destination))

        try:
            while self.current_floor != destination:

                # determine traveling time for 1 floor
                t = self.travelingTime(destination, self.current_floor, source)
                yield self.env.timeout(t)
                self.total_movement += 1

                # advance 1 floor
                self.current_floor = self.forwards(self.current_floor, self.direction)
                self.moveFloorNum += 1

                if(self.elev_logger != None):
                    self.elev_logger.log_arrive(
                        self.elev_name, self.direction, self.current_floor, float(self.env.now))

                logging.info('[MOVING] Elev {}, Update To {} Floor'.format(
                    self.elev_name, self.current_floor))

        except simpy.Interrupt:
            pass
            logging.info(
                '[MOVING] Elev {}, Interrupted'.format(self.elev_name))
            logging.debug('[MOVING] Elev {}, stop_list {}'.format(
                self.elev_name, self.stop_list))

    def serving(self):
        isServed = False

        # deal with statistic
        self.stopNum += 1

        # remove from schedule
        self.stop_list.pop(self)
        logging.info('[SERVING] Elev {}, after pop:{}'.format(self.elev_name, self.stop_list))

        # customers leave
        leaveCount = 0
        transfer_customers= []
        for i in range(len(self.riders)-1, -1, -1):
            customer = self.riders.pop(i)
            if customer.temp_destination ==  self.current_floor:
                transfer_customers.append(customer)
                if(self.customer_logger != None):
                    self.customer_logger.log_get_off(customer.cid, self.current_floor, float(self.env.now))

            elif customer.destination == self.current_floor:
                # do nothing
                if(self.customer_logger != None):
                    self.customer_logger.log_get_off(customer.cid, self.current_floor, float(self.env.now))

            leaveCount += 1
        if leaveCount > 0:
            isServed = True

        yield self.env.timeout(leaveCount*1)

        logging.info('[SERVING] Elev {}, {} Customers Leave'.format(
            self.elev_name, leaveCount))

        if transfer_customers:
            self.EVENT.ELEV_TRANSFER[self.direction][self.current_floor].succeed(value=transfer_customers)
            self.EVENT.ELEV_TRANSFER[self.direction][self.current_floor] = self.env.event()

        # exclude 'peak' condition
        if not((self.current_floor == self.floorList[-1] and self.direction == 1) or
               (self.current_floor == self.floorList[0] and self.direction == -1)):

            # elevator arrive
            self.EVENT.ELEV_ARRIVAL[self.direction][self.current_floor].succeed(value=(self.capacity-len(self.riders), self.elev_name))
            self.EVENT.ELEV_ARRIVAL[self.direction][self.current_floor] = self.env.event()
            
            # customers on board
            riders = yield self.EVENT.ELEV_LEAVE[self.elev_name]
            
            if riders:
                isServed = True

            logging.info('[SERVING] Elev {}, Customers Aboard: \n {}'.format(
                self.elev_name, [vars(i) for i in riders]))

            # add inner calls
            for customer in riders:
                destination = customer.select_destination(self.current_floor, self.direction,  self.infeasible)
                self.stop_list.pushInner(self, destination)

            self.riders = self.riders + riders

            if(self.elev_logger != None):
                self.elev_logger.log_serve(self.elev_name, len(
                    self.riders), self.direction, self.current_floor, float(self.env.now))

        # determine direction
        nextTarget = self.stop_list.next_target(self)
        logging.info('[SERVING] Elev {}, NEXT TARGET {}'.format(
            self.elev_name, nextTarget))

        if nextTarget == None:
            logging.debug('[SERVING] Elev {}, nextTarget is None, {}'.format(
                self.elev_name, nextTarget))
            return
        else:
            logging.debug('[SERVING] Elev {}, currFloor {}, nextTarget {}'.format(
                self.elev_name, self.current_floor, nextTarget))


            if displacement(self.current_floor, nextTarget) > 0:
                self.direction = 1
            elif displacement(self.current_floor, nextTarget) < 0:
                self.direction = -1
            else:
                # make a turn
                self.direction = -1*self.direction
                self.stop_list.pop(self)

                # customers on board
                self.EVENT.ELEV_ARRIVAL[self.direction][self.current_floor].succeed(value=(self.capacity-len(self.riders), self.elev_name))
                self.EVENT.ELEV_ARRIVAL[self.direction][self.current_floor] = self.env.event()

                # new customers
                riders = yield self.EVENT.ELEV_LEAVE[self.elev_name]

                if riders:
                    isServed = True

                logging.info('[SERVING] Elev {}, Customers Aboard: \n {} '.format(
                    self.elev_name, [vars(i) for i in riders]))

                for customer in riders:
                    self.stop_list.pushInner(self, customer.select_destination(self.current_floor, self.direction, self.infeasible))
                
                self.riders = self.riders + riders

                if(self.elev_logger != None):
                    self.elev_logger.log_serve(
                        self.elev_name, len(self.riders), self.direction, self.current_floor, float(self.env.now))

                if not isServed:
                    self.wasteStopNum += 1

    def travelingTime(self, destination, current, source):
        # acceleration should be considered
        return ELEV_CONFIG.ELEV_VELOCITY

    @staticmethod
    def mission_priority(mission):
        floor = mission.destination
        direction = mission.direction
        index = int(floor) if not 'B' in floor else -int(floor[1:]) + 1
        index = index*direction
        return index

    @staticmethod
    def forwards(floor, direction):
        floor = int(floor) if not 'B' in floor else -int(floor[1:]) + 1
        floor += direction
        floor = str(floor) if floor > 0 else "B{}".format(abs(floor-1))
        return floor