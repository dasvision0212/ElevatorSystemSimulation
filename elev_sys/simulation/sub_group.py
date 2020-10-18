import logging
import pandas as pd

from elev_sys.conf.elevator_conf import ELEV_CONFIG
from elev_sys.simulation.elevator import Elevator
from elev_sys.simulation.simple_data_structure import Mission
from elev_sys.simulation.logger import (Customer_logger, Elev_logger, StopList_logger)
import elev_sys.simulation.utils as utils


class SubGroup:
    def __init__(self, env, floorList,  sub_group_name, sub_group_setting, EVENT, 
                 customer_logger:Customer_logger = None, elev_logger:Elev_logger = None, stopList_logger:StopList_logger=None):        
        self.env = env
        self.EVENT = EVENT
        
        self.sub_group_name = sub_group_name

        self.elevators = dict()
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

        if(isinstance(ELEV_CONFIG.VERSION, int)):

            # Penalty
            DIFFERENT_DIR_BIAS = 10
            SAME_DIR_BACK_BIAS = 20

            # Initial
            minDistance = 1000

            logging.warning("Mission: dir {}, des {}".format(direction, source))

            # elevators that can arrive the mission destination
            elevators = [elevator for elevator in self.elevators.values() if not elevator.stop_list.isNA(direction, source)]

            for elevator in elevators:

                # condition
                isSameDirection = direction == elevator.direction
                isCustomerAhead = utils.displacement(elevator.current_floor, source) * direction > 0
                isElevIdle = (elevator.direction == 0)
                
                # cost function
                dispatching_cost = 0

                # mission destination is ahead of the elevator
                ## (down)       
                ## ( up )     [E]→　　→   (M)→  
                if ( isSameDirection & isCustomerAhead | isElevIdle):
                    distance = abs(utils.displacement(source, elevator.current_floor)) 
                    dispatching_cost = distance
                
                # mission destination is not in the direction with the elevator
                ## (down)     ←(M)　　　 ←　      ←
                ## ( up )       →    [E]→      →  ↑
                elif not isSameDirection:
                    dispatching_cost  = DIFFERENT_DIR_BIAS + utils.displacement(elevator.current_floor, source) * elevator.direction

                # mission destination is behind the elevator
                ## (down) ↓     ←　　　  　←　　　 ←　
                ## ( up ) →  (M)→    [E]→      →  ↑
                elif isSameDirection & (not isCustomerAhead):
                    dispatching_cost  = SAME_DIR_BACK_BIAS + utils.displacement(elevator.current_floor, source) * -elevator.direction
                
                ## ONLY IN THIS FLOOR PARTITION SCHEMA
                if utils.advance(source, direction) in elevator.infeasible:
                    dispatching_cost += 1000

                if(dispatching_cost < minDistance):
                    bestElevator = elevator.elev_name
                    minDistance = dispatching_cost

                logging.warning(elevator.elev_name)
                logging.warning("dir: {}, curr: {}".format(elevator.direction, elevator.current_floor))
                logging.warning("score: {}".format(dispatching_cost))

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
                "waste_stop_num"   : elevator.wasteStopNum, 
                "move_floor_num": elevator.moveFloorNum
            })
        
        return pd.DataFrame(statistics)