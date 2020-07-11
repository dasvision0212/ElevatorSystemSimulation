import logging
import random

from elev_sim.elevator.elevator import Elevator, displacement
from elev_sim.elevator.simple_data_structure import Mission
from elev_sim.elevator.logger import (Customer_logger, Elev_logger)

class ElevatorController:
    def __init__(self, env, elevatorList, floorList, EVENT, customer_logger:Customer_logger = None, elev_logger:Elev_logger = None):
        self.env = env
        self.elevatorList = elevatorList
        self.elevators = dict()
        self.EVENT = EVENT

        for elevatorName in elevatorList:
            self.elevators[elevatorName] = Elevator(env, elevatorName, floorList, self.EVENT, customer_logger, elev_logger)
        self.env.process(self.assignCalls())



    def assignCalls(self):
        while True:
            mission = yield self.EVENT.CALL

            candidate = random.choices(self.elevatorList, weights=[1/len(self.elevatorList)] * len(self.elevatorList))[0]
            self.elevators[candidate].assign_event.succeed(value=mission)

            yield self.elevators[candidate].finish_event
            logging.info('[AssignCalls] Succeed')

    def bestCandidate(self, direction, source):
        '''Assignment Policy'''
        minDistance = 50
        bestElevator = str()
        for elevator in self.elevators.values():
            if (minDistance > abs(displacement(source, elevator.current_floor)) and
                ((direction == elevator.direction and elevator.current_floor*direction < direction*source)
                    or elevator.direction == 0)):
                minDistance = abs(displacement(source, elevator.current_floor))
                bestElevator = elevator.elevIndex

        if minDistance == 50:
            self.failAssignment.append(
                Mission(direction=direction, destination=source))
            # raise AssignmentError()

        return bestElevator