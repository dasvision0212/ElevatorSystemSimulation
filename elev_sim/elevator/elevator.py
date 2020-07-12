import simpy
import random
from copy import deepcopy
import logging

from elev_sim.conf.elevator_conf import ELEV_CONFIG, ELEVLOG_CONFIG
from elev_sim.elevator.simple_data_structure import Mission
from elev_sim.elevator.event import Event
from elev_sim.elevator.logger import Elev_logger, Customer_logger


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

    def __init__(self, FloorList):
        self.floorList = deepcopy(FloorList)

        self._list = {
             1: [0] * (len(FloorList)),
            -1: [0] * (len(FloorList))
        }

        # dictionary for indexing
        self.index = {
            1: {floor: index for index, floor in enumerate(FloorList)},
            -1: {floor: index for index, floor in enumerate(reversed(FloorList))}
        }
        self.reversed_index = {
            1: {index: floor for index, floor in enumerate(FloorList)},
            -1: {index: floor for index, floor in enumerate(reversed(FloorList))}
        }

    def __str__(self):
        string = 'Stop List: \n  up   down \n'
        sss = ['{} [{}] [{}] {}\n'.format(f, i, j, f) for f, i, j in zip(
            self.floorList, self._list[1], self._list[-1])]
        string.join(sss)
        return str(self._list)
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

    def pushInner(self, elev, destination):
        currentIndex = self.index[elev.direction][destination]

        # illegal index
        if self._list[elev.direction][currentIndex] == StopList.NA:
            raise IndexError()

        # add inner call to stoplist
        self._list[elev.direction][currentIndex] = StopList.ACTIVE

    def pop(self, elev):
        currentIndex = self.index[elev.direction][elev.current_floor]

        # illegal index
        if self._list[elev.direction][currentIndex] == StopList.NA:
            raise IndexError()

        # remove target floor from stoplist
        self._list[elev.direction][currentIndex] = StopList.IDLE
        logging.debug('[POP] ele {}, curFlo {}, dir {}'.format(
            elev.elevIndex, elev.current_floor, elev.direction))

    def next_target(self, elev):
        current_floor = elev.current_floor
        if current_floor == 'B2':
            current_floor = Elevator.forwards(current_floor, elev.direction)

        v = 3
        if v == 3:
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

        if v == 2:
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


class Elevator:
    def __init__(self, env, elevIndex, floorList, EVENT: Event,
                 customer_logger: Customer_logger = None, elev_logger: Elev_logger = None):
        self.env = env
        self.elevIndex = str(elevIndex)
        self.capacity = ELEV_CONFIG.ELEV_CAPACITY
        self.riders = []
        self.EVENT = EVENT
        self.floorList = floorList

        # schedule list
        self.stop_list = StopList(self.floorList)

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

    def idle(self):
        logging.info('[IDLE] Elev {} Activated'.format(self.elevIndex))
#         print('[IDLE] Elevator {} Activated'.format(self.elevIndex))

        while True:
            if(self.elev_logger != None):
                self.elev_logger.log_idle(
                    self.elevIndex, self.current_floor, float(self.env.now))

            # first assignment
            mission = yield self.assign_event
            logging.debug(
                '[Assign_event - idle] Elev {}, stopList {}'.format(self.elevIndex, self.stop_list))

            # reactivate
            self.assign_event = self.env.event()
            self.finish_event.succeed()
            self.finish_event = self.env.event()

            logging.info('[IDLE] Elev {}, Outer Call: {}'.format(
                self.elevIndex, mission))

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
            logging.info('[IDLE] Elev {} Stopped.'.format(self.elevIndex))

            # return to IDLE state
            self.direction = 0

    def onMission(self):
        while not self.stop_list.isEmpyty():
            #             print(self.stop_list)

            nextTarget = self.stop_list.next_target(self)
#             logging.info('[ONMISSION] NEXT TARGET {}'.format(nextTarget))
            logging.info('[ONMISSION] Elev {}, NEXT TARGET {}'.format(
                self.elevIndex, nextTarget))
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
                        self.elevIndex, mission))

                    before = nextTarget

                    self.stop_list.pushOuter(
                        self, mission.direction, mission.destination)
                    logging.debug('[ONMISSION] Elev {}, STOP LIST {}'.format(
                        self.elevIndex, self.stop_list))

                    nextTarget = self.stop_list.next_target(self)
                    logging.info('[ONMISSION] Elev {}, NEXT TARGET {}'.format(
                        self.elevIndex, nextTarget))

                    if before != nextTarget:
                        moving_proc.interrupt()
                        moving_proc = self.env.process(
                            self.moving(nextTarget, self.current_floor))

            logging.info('[ONMISSION] Elev {}, Arrive At {} Floor'.format(
                self.elevIndex, self.current_floor))
            yield self.env.process(self.serving())
            logging.info('[Afer Serving] Elev {}, rider {}'.format(
                self.elevIndex, [(vars(i)) for i in self.riders]))

    def moving(self, destination, source):
        """source is needed to account for the acceleration and deceleration rate of the elevator"""
        logging.info('[MOVING] Elev {}, Moving Process Started: to {}'.format(
            self.elevIndex, destination))

        try:
            while self.current_floor != destination:

                # determine traveling time for 1 floor
                t = self.travelingTime(destination, self.current_floor, source)
                yield self.env.timeout(t)

                # advance 1 floor
                self.current_floor = self.forwards(
                    self.current_floor, self.direction)

                if(self.elev_logger != None):
                    self.elev_logger.log_arrive(
                        self.elevIndex, self.direction, self.current_floor, float(self.env.now))

                logging.info('[MOVING] Elev {}, Update To {} Floor'.format(
                    self.elevIndex, self.current_floor))

        except simpy.Interrupt:
            pass
            logging.info(
                '[MOVING] Elev {}, Interrupted'.format(self.elevIndex))
            logging.debug('[MOVING] Elev {}, stop_list {}'.format(
                self.elevIndex, self.stop_list))

    def serving(self):

        # remove from schedule
        self.stop_list.pop(self)
        logging.info('[SERVING] Elev {}, after pop:{}'.format(
            self.elevIndex, self.stop_list))

        # customers leave
        leaveCount = 0
        for i in range(len(self.riders)-1, -1, -1):
            if self.riders[i].destination == self.current_floor:

                customer = self.riders.pop(i)
                customer.leave_time = float(self.env.now)
                if(self.customer_logger != None):
                    self.customer_logger.log(customer)

                leaveCount += 1
        yield self.env.timeout(leaveCount*1)
        logging.info('[SERVING] Elev {}, {} Customers Leave'.format(
            self.elevIndex, leaveCount))

        # exclude 'peak' condition
        if not((self.current_floor == self.floorList[-1] and self.direction == 1) or
               (self.current_floor == self.floorList[0] and self.direction == -1)):

            # elevator arrive
            self.EVENT.ELEV_ARRIVAL[self.direction][self.current_floor].succeed(
                value=(self.capacity-len(self.riders), self.elevIndex))
            self.EVENT.ELEV_ARRIVAL[self.direction][self.current_floor] = self.env.event(
            )

            # customers on board
            riders = yield self.EVENT.ELEV_LEAVE[self.elevIndex]
            logging.info('[SERVING] Elev {}, Customers Aboard: \n {}'.format(
                self.elevIndex, [vars(i) for i in riders]))

            # add inner calls
            for customer in riders:

                self.stop_list.pushInner(self, customer.destination)
            self.riders = self.riders + riders

            if(self.elev_logger != None):
                self.elev_logger.log_serve(self.elevIndex, len(
                    self.riders), self.direction, self.current_floor, float(self.env.now))

        # determine direction
        nextTarget = self.stop_list.next_target(self)
        logging.info('[SERVING] Elev {}, NEXT TARGET {}'.format(
            self.elevIndex, nextTarget))

        if nextTarget == None:
            logging.debug('[SERVING] Elev {}, nextTarget is None, {}'.format(
                self.elevIndex, nextTarget))
            return
        else:
            logging.debug('[SERVING] Elev {}, currFloor {}, nextTarget {}'.format(
                self.elevIndex, self.current_floor, nextTarget))
            if displacement(self.current_floor, nextTarget) > 0:
                #                 print('change direction: up')
                self.direction = 1
            elif displacement(self.current_floor, nextTarget) < 0:
                #                 print('change direction: down')
                self.direction = -1
            else:
                # make a turn
                self.direction = -1*self.direction
                self.stop_list.pop(self)

                # customers on board
                self.boarding()

                if(self.elev_logger != None):
                    self.elev_logger.log_serve(
                        self.elevIndex, len(self.riders), self.direction, self.current_floor, float(self.env.now))

    def travelingTime(self, destination, current, source):
        # acceleration should be considered
        return 10

    def boarding(self):
        # boarding
        self.EVENT.ELEV_ARRIVAL[self.direction][self.current_floor].succeed(
            value=(self.capacity-len(self.riders), self.elevIndex))
        self.EVENT.ELEV_ARRIVAL[self.direction][self.current_floor] = self.env.event(
        )

        riders = yield self.EVENT.ELEV_LEAVE[self.elevIndex]
        logging.info('[SERVING] Elev {}, Customers Aboard: \n {} '.format(
            self.elevIndex, [vars(i) for i in riders]))
#         print('[SERVING] Customers Aboard: \n  ', riders)

        # new customers
        for customer in riders:
            self.stop_list.pushInner(self, customer.destination)
        self.riders = self.riders + riders

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