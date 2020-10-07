import logging
import random
import pandas as pd

from elev_sys.conf.elevator_conf import ELEV_CONFIG
from elev_sys.simulation.elevator import Elevator, displacement
from elev_sys.simulation.simple_data_structure import Mission
from elev_sys.simulation.logger import (Customer_logger, Elev_logger, StopList_logger)


class SubGroup:
    def __init__(self, env, floorList,  sub_group_name, sub_group_setting, EVENT, 
                 customer_logger:Customer_logger = None, elev_logger:Elev_logger = None, stopList_logger:StopList_logger=None):
        '''
        @param setting: tuple(sub_group_name, { "infeasible":["1", "15"], 
                                                "elevNum": 2})
        '''
        
        self.env = env
        self.EVENT = EVENT

        self.elevators = dict()
        self.sub_group_name = sub_group_name
        for i in range(len(sub_group_setting["infeasibles"])):
            elev_name = sub_group_name + str(i)
            self.elevators[elev_name] = Elevator(env, elev_name, floorList, sub_group_setting["infeasibles"][i], self.EVENT, 
                                                    customer_logger=customer_logger, 
                                                    elev_logger=elev_logger, 
                                                    stopList_logger=stopList_logger)
        self.env.process(self.assignCalls())


    def assignCalls(self):
        while True:
            mission = yield self.EVENT.CALL[self.sub_group_name]

            # candidate = random.choices(self.elevNameList, weights=[1/len(self.elevNameList)] * len(self.elevNameList))[0]
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
                    
                if source in elevator.infeasible:
                    elevator_score += 50000000

                if(elevator_score < minDistance):
                    bestElevator = elevator.elev_name
                    minDistance = elevator_score

                logging.warning(elevator.elev_name)
                logging.warning("dir: {}, curr: {}".format(elevator.direction, elevator.current_floor))
                logging.warning("score: {}".format(elevator_score))

        logging.warning("best: {}".format(bestElevator))
        logging.warning("---------------------------------------------")

        return bestElevator

    def get_statistics(self):
        statistics = list()
        for elev_name, elevator in self.elevators.items():
            statistics.append({
                "sub_group" : self.sub_group_name, 
                "elevator"  : elev_name,  
                "stop_num"   : elevator.stopNum, 
                "move_floor_num": elevator.moveFloorNum
            })
        
        return pd.DataFrame(statistics)