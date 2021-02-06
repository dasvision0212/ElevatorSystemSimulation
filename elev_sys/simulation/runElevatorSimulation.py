from elev_sys.simulation.path_finder import Path_finder
from elev_sys.simulation import path_finder
import simpy
import random
import numpy as np
import pandas as pd
import sys
sys.path.append('../')

from elev_sys.simulation.floor import Floor
from elev_sys.simulation.event import Event

from elev_sys.simulation.elevator_group import Elevator_group
from elev_sys.simulation.logger import Customer_logger, Elev_logger, Queue_logger, StopList_logger

import logging

def runElevatorSimulation(env, IAT_D, destination_dist, floorList, group_setting, 
                          randomSeed,
                          untilTime = 4400,
                          cid_gen=None, 
                          customer_logger:Customer_logger=None, 
                          elev_logger:Elev_logger=None, 
                          queue_logger:Queue_logger=None, 
                          stopList_logger:StopList_logger=None):


    # initialization
    event = Event(env, floorList, group_setting)
    path_finder = Path_finder(floorList, group_setting)#, fileName="./path_log.json")
    
    # process
    floors = [Floor(env, floorList, floorName, floorIndex, IAT_D,
                destination_dist.loc[floorName], group_setting, cid_gen, event, path_finder,
                queue_logger=queue_logger, customer_logger=customer_logger) 
                for floorIndex, floorName in enumerate(floorList)]

    elevator_group = Elevator_group(env, group_setting, floorList, event, 
                                    customer_logger=customer_logger, 
                                    elev_logger=elev_logger, 
                                    stopList_logger=stopList_logger)
    print('run time',untilTime)
    env.run(until=untilTime)
    return elevator_group.get_statistics()