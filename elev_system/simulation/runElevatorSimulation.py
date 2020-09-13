import simpy
import random
import pandas as pd
import sys
sys.path.append('../')

from elev_sim.simulation.floor import Floor
from elev_sim.simulation.event import Event
from elev_sim.simulation.elevator_ctrl import ElevatorController
from elev_sim.simulation.IAT_Distribution import IAT_Distribution
from elev_sim.simulation.logger import Customer_logger, Elev_logger, Queue_logger, StopList_logger
from elev_sim.conf.NTUH_conf import ELEVATOR_GROUP

import logging

def runElevatorSimulation(env, Dist_InterArrival, Ratio_byFloor, location, timeSection, floorList, elevatorList,
                          randomSeed, floorNum, untilTime, cid_gen=None, 
                          customer_logger:Customer_logger=None, 
                          elev_logger:Elev_logger=None, 
                          queue_logger:Queue_logger=None, 
                          stopList_logger:StopList_logger=None):
    random.seed(randomSeed)
    IAT_D = IAT_Distribution(Dist_InterArrival)
    DD    = pd.read_csv(Ratio_byFloor).iloc[:, 1:].set_index('from').iloc[0:floorNum+1, 0:floorNum+1]
    DD    = DD.drop(['B2'], axis=1).drop(['B2'], axis=0) # !!!!!! not reusable

    event = Event(env, floorList, elevatorList)
    # process
    floors_upward = [Floor(env, floorName, floorIndex, 1, IAT_D.getter(location, timeSection, 'up', floorName), 
                            DD.loc[floorName][floorName.lstrip("0"):], cid_gen, event, queue_logger=queue_logger) \
                                for floorIndex, floorName in enumerate(floorList[:-1]) \
                                if IAT_D.getter(location, timeSection, 'up', floorName)  != None]
    floors_downward = [Floor(env, floorName, floorIndex, -1, IAT_D.getter(location, timeSection, 'down', floorName), 
                            DD.loc[floorName][:floorName.lstrip("0")], cid_gen, event, queue_logger=queue_logger) \
                                for floorIndex, floorName in enumerate(floorList[1:]) \
                                if IAT_D.getter(location, timeSection, 'up', floorName) != None]
    elevator_ctrl = ElevatorController(env, elevatorList, floorList, event, 
                                       customer_logger=customer_logger, 
                                       elev_logger=elev_logger, 
                                       stopList_logger=stopList_logger)
    env.run(until=untilTime)