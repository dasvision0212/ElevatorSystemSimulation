import logging
import pandas as pd
import random

from elev_sys.conf.elevator_conf import ELEV_CONFIG
from elev_sys.simulation.elevator import Elevator
from elev_sys.simulation.simple_data_structure import Mission
from elev_sys.simulation.logger import (Customer_logger, Elev_logger, StopList_logger)
from elev_sys.simulation.utils import cal_displacement, advance


class SubGroup:
    def __init__(self, env, floorList,  sub_group_name, sub_group_setting, EVENT, 
                 customer_logger:Customer_logger = None, elev_logger:Elev_logger = None, stopList_logger:StopList_logger=None):        
        self.env = env
        self.EVENT = EVENT
        
        self.sub_group_name = sub_group_name

        self.elevators = dict()
        for i in range(len(sub_group_setting["available_floor"])):
            elev_name = sub_group_name + str(i)
            self.elevators[elev_name] = Elevator(env, elev_name, floorList, sub_group_setting["available_floor"][i], self.EVENT, 
                                                    customer_logger=customer_logger, 
                                                    elev_logger=elev_logger, 
                                                    stopList_logger=stopList_logger)
        self.env.process(self.assignCalls())


    def assignCalls(self):
        while True:
            mission = yield self.EVENT.CALL[self.sub_group_name]

            # decide candidate given the call's floor and direction
            candidate = self.bestCandidate(mission)
            
            # pass call over to elevator
            self.elevators[candidate].ASSIGN_EVENT.succeed(value=mission)
            yield self.elevators[candidate].FINISH_EVENT
            
            logging.info('[AssignCalls] Succeed')


    def bestCandidate(self, mission):
        '''Assignment Policy'''
        bestElevator = str()
        direction, source = mission

        if(ELEV_CONFIG.VERSION == 3):
            bestElevator = self._assign_v3(mission)
        if(ELEV_CONFIG.VERSION == 4):
            bestElevator = self._assign_v4(mission)


        logging.warning("best: {}".format(bestElevator))
        logging.warning("---------------------------------------------")

        return bestElevator


    def _assign_v4(self, mission, randomPolicy_prob=0.3):
        if(random.random() < randomPolicy_prob):
            direction, source = mission
            elev_candidate = [elevName for elevName, elevator in self.elevators.items()\
                                        if not elevator.stop_list.isNA(direction, source)]
            elevIndex = random.randint(0, len(elev_candidate)-1)

            return elev_candidate[elevIndex]
        else:
            return self._assign_v3(mission)

    
    def _assign_v3(self, mission):
        '''
         Assignment Policy version3
        '''
        bestElevator = str()
        direction, source = mission

        # Penalty
        DIFFERENT_DIR_BIAS = 10
        SAME_DIR_BACK_BIAS = 20

        # Initial
        min_dispatching_cost = None

        logging.warning("Mission: dir {}, des {}".format(direction, source))

        # elevators that can arrive the mission destination
        elevators = [elevator for elevator in self.elevators.values() if not elevator.stop_list.isNA(direction, source)]
        for elevator in elevators:
            # condition
            isSameDirection = (direction == elevator.direction)
            isCustomerAhead = cal_displacement(elevator.current_floor, source) * direction > 0
            isElevIdle = (elevator.direction == 0)
            
            # cost function
            dispatching_cost = 0

            # mission destination is ahead of the elevator
            ## (down)       
            ## ( up )     [E]→　　→   (M)→  
            if ((isSameDirection and isCustomerAhead) or isElevIdle):
                distance = abs(cal_displacement(source, elevator.current_floor)) 
                dispatching_cost = distance
            
            # mission destination is not in the direction with the elevator
            ## (down)     ←(M)　　　 ←　      ←
            ## ( up )       →    [E]→      →  ↑
            elif not isSameDirection:
                dispatching_cost  = DIFFERENT_DIR_BIAS + cal_displacement(elevator.current_floor, source) * elevator.direction

            # mission destination is behind the elevator
            ## (down) ↓     ←　　　  　←　　　 ←　
            ## ( up ) →  (M)→    [E]→      →  ↑
            elif isSameDirection & (not isCustomerAhead):
                dispatching_cost  = SAME_DIR_BACK_BIAS + cal_displacement(elevator.current_floor, source) * -elevator.direction
            
            oneStep = advance(source, direction)
            if (source == elevator.available_floor[-1] and direction == 1) or \
               (source == elevator.available_floor[0] and direction == -1):
                continue

            if(min_dispatching_cost is None) or (dispatching_cost < min_dispatching_cost):
                bestElevator = elevator.elev_name
                min_dispatching_cost = dispatching_cost

            logging.warning(elevator.elev_name)
            logging.warning("dir: {}, curr: {}".format(elevator.direction, elevator.current_floor))
            logging.warning("score: {}".format(dispatching_cost))
            
            
        return bestElevator


    def get_statistics(self):
        statistics = list()
        for elev_name, elevator in self.elevators.items():
            statistics.append({
                "sub_group" : self.sub_group_name, 
                "elevator"  : elev_name,  
                "stop_num"   : elevator.stopNum, 
                "waste_stop_num"   : elevator.wasteStopNum, 
                "move_floor_num": elevator.moveFloorNum
            })
        
        return pd.DataFrame(statistics)