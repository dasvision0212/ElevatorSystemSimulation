import logging
import pandas as pd
import random

from elev_sys.conf.elevator_conf import ELEV_CONFIG
from elev_sys.simulation.elevator import Elevator, StopList
from elev_sys.simulation.logger import (Customer_logger, Elev_logger, StopList_logger)
from elev_sys.simulation.utils import cal_displacement, Mission


class SubGroup:
    def __init__(self, env, floorList,  sub_group_name, sub_group_setting, EVENT, 
                 customer_logger:Customer_logger = None, elev_logger:Elev_logger = None, stopList_logger:StopList_logger=None):        
        self.env = env
        self.EVENT = EVENT
        
        self.sub_group_name = sub_group_name
        self.floorList = floorList
        self._list = {
             1: [False] * (len(floorList)),
            -1: [False] * (len(floorList))
        }

        self.elevators = dict()
        for i in range(len(sub_group_setting["available_floor"])):
            elev_name = sub_group_name + str(i)
            self.elevators[elev_name] = Elevator(env, elev_name, floorList, sub_group_setting["available_floor"][i], self.EVENT, 
                                                    sub_group = self,
                                                    customer_logger=customer_logger, 
                                                    elev_logger=elev_logger, 
                                                    stopList_logger=stopList_logger)
        

        self.env.process(self.assignCalls())

    #     self.env.process(self.debug())
    # def debug(self):
    #     while True:
    #         yield self.env.timeout(100)
    #         print('C',self.elevators['a4'].ASSIGN_EVENT)
    def delayAssign(self, candidate, mission):
        last_floor = self.elevators[candidate].current_floor
        while True:
            yield self.env.timeout(0.1)
            if last_floor != self.elevators[candidate].current_floor:
                self.elevators[candidate].ASSIGN_EVENT.succeed(value=mission)
                self.elevators[candidate].ASSIGN_EVENT = self.env.event()
                break
        
        # left_time_to_move = ELEV_CONFIG.ELEV_VELOCITY - \
        #                     (self.env.now - self.elevators[candidate].move_start_time) + \
        #                     ELEV_CONFIG.ELEV_VELOCITY_BUFFER + ELEV_CONFIG.ELEV_CLOSE
        # yield self.env.timeout(left_time_to_move)

        # self.elevators[candidate].ASSIGN_EVENT.succeed(value=mission)
        # self.elevators[candidate].ASSIGN_EVENT = self.env.event()

    def assignCalls(self):
        while True:
            candidate = None

            mission = yield self.EVENT.CALL[self.sub_group_name]
             
            # handle repeated
            direction, destination = mission

            # decide candidate given the call's floor and direction
            candidate = self.bestCandidate(mission)
            print(f'{self.env.now} 3.[CONTROL] mission {mission}')
            
            # pass call over to elevator
            if self.elevators[candidate].direction == 0:
                self.elevators[candidate].ASSIGN_EVENT.succeed(value=mission)
                self.elevators[candidate].ASSIGN_EVENT = self.env.event()

                print(f'{self.env.now} 4.[ASSIGN] candidate {candidate} (idle)')

            elif destination == self.elevators[candidate].current_floor:
                if not self.elevators[candidate].isServing:
                    self.env.process(self.delayAssign(candidate, mission))
                    print(f'{self.env.now} 4.[ASSIGN] candidate {candidate} (not serving & same)')
                else:
                    self.EVENT.buttonPushed[mission.destination][self.sub_group_name] = False
                    print(f'{self.env.now} 4.[ASSIGN] candidate {candidate} (serving & same)')
            else:    
                self.elevators[candidate].ASSIGN_EVENT.succeed(value=mission)
                self.elevators[candidate].ASSIGN_EVENT = self.env.event()

                print(f'{self.env.now} 4.[ASSIGN] candidate {candidate} (onmission)')

            logging.info('[AssignCalls] Succeed')


    def bestCandidate(self, mission):
        '''Assignment Policy'''
        bestElevator = str()
        direction, source = mission

        bestElevator = self._assign_v3(mission)

        logging.warning("best: {}".format(bestElevator))
        logging.warning("---------------------------------------------")

        return bestElevator

    
    def _assign_v3(self, mission):
        '''
         Assignment Policy version3
        '''
        bestElevator = str()
        direction, source = mission

        # Penalty
        DIFFERENT_DIR_BIAS = 20
        SAME_DIR_BACK_BIAS = 40

        # Initial
        min_dispatching_cost = None

        logging.warning("Mission: dir {}, des {}".format(direction, source))

        # elevators that can arrive the mission destination
        # 多篩一次
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
            

            # 分層+連控 (!!!!!!!)
            if (source == elevator.available_floor[-1] and direction == 1) or \
               (source == elevator.available_floor[0] and direction == -1):
                dispatching_cost += 50

            ## full condition
            # if elevator.capacity - len(elevator.riders) < 1:
            #     dispatching_cost += 100

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