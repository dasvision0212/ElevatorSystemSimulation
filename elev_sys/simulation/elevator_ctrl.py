import logging
import random

from elev_sys.conf.elevator_conf import ELEV_CONFIG
from elev_sys.simulation.elevator import Elevator, displacement
from elev_sys.simulation.simple_data_structure import Mission
from elev_sys.simulation.logger import (Customer_logger, Elev_logger, StopList_logger)


class ElevatorController:
    def __init__(self, env, elevatorList, floorList, EVENT, 
                 customer_logger:Customer_logger = None, elev_logger:Elev_logger = None, stopList_logger:StopList_logger=None):
        self.env = env
        self.elevatorList = elevatorList
        self.elevators = dict()
        self.EVENT = EVENT

        for elevatorName in elevatorList:
            self.elevators[elevatorName] = Elevator(env, elevatorName, floorList, self.EVENT, 
                                                    customer_logger=customer_logger, 
                                                    elev_logger=elev_logger, 
                                                    stopList_logger=stopList_logger)
        self.env.process(self.assignCalls())


    def assignCalls(self):
        while True:
            mission = yield self.EVENT.CALL

            # candidate = random.choices(self.elevatorList, weights=[1/len(self.elevatorList)] * len(self.elevatorList))[0]
            candidate = self.bestCandidate(mission)
            self.elevators[candidate].assign_event.succeed(value=mission)

            yield self.elevators[candidate].finish_event
            logging.info('[AssignCalls] Succeed')


    def bestCandidate(self, mission):
        '''Assignment Policy'''
        bestElevator = str()
        direction, source = mission

        if(isinstance(ELEV_CONFIG.VERSION, int)):
            DIFFERENT_DIR_BASE = 1000
            SAME_DIR_BACK_BASE = 2000

            minDistance = 50000000
            logging.warning("Mission: dir {}, des {}".format(direction, source))

            elevators = [elevator for elevator in self.elevators.values() if not elevator.stop_list.isNA(direction, source)]

            for elevator in elevators:
                elevator_score = int()
                if ((direction == elevator.direction and displacement(elevator.current_floor, source) * direction > 0) \
                    or (elevator.direction == 0)):
                    elevator_score = abs(displacement(source, elevator.current_floor))
                
                elif(direction != elevator.direction):
                    elevator_score  = DIFFERENT_DIR_BASE + displacement(elevator.current_floor, source) * elevator.direction

                # we should notice that the situation of the same direction and same floor belongs to this block
                elif(direction == elevator.direction and displacement(elevator.current_floor, source) * direction <= 0):
                    elevator_score  = SAME_DIR_BACK_BASE + displacement(elevator.current_floor, source) * -elevator.direction
                    
                if(elevator_score < minDistance):
                    bestElevator = elevator.elevIndex
                    minDistance = elevator_score

                logging.warning(elevator.elevIndex)
                logging.warning("dir: {}, curr: {}".format(elevator.direction, elevator.current_floor))
                logging.warning("score: {}".format(elevator_score))

        logging.warning("best: {}".format(bestElevator))
        logging.warning("---------------------------------------------")

        return bestElevator