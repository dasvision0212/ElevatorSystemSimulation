import simpy
import numpy.random as random
import pandas as pd
import json
import sys
sys.path.append('../')

from elev_system import *
from elev_system.conf.NTUH_conf import ELEVATOR_GROUP, BUILDING_FLOOR, ELEV_INFEASIBLE
import logging
from os.path import join as joinPath

if(__name__ == "__main__"):
    logging.basicConfig(level=logging.WARNING)
    untilTime = 2000

    Dist_InterArrival = '../data/BestFitDistribution.csv'
    timeSection = 2
    
    # Variable
    Ratio_byFloor = {"北棟病床": '../data/FloorRatio_NHB.csv',
                     "研究大樓": '../data/FloorRatio_Research.csv',
                     "南棟客梯": '../data/FloorRatio_SC.csv' , 
                     "南棟病床": '../data/FloorRatio_SHB.csv'}

    location = ["北棟病床", "研究大樓", "南棟客梯", "南棟病床"][0]

    Statistic_df = []
    elevatorList = ELEVATOR_GROUP[location]
    floorList    = BUILDING_FLOOR[location]

    # Enviornment Variable
    env = simpy.Environment()
    cid_gen = cid_generator()
    randomSeed = int(random.rand(1)*10000)
    
    # Global
    customer_logger = Customer_logger(status=True)
    elev_logger = Elev_logger(status=True)
    queue_logger = Queue_logger(status=True)
    stopList_logger = StopList_logger(status=True)

    runElevatorSimulation(env, Dist_InterArrival, Ratio_byFloor[location], location, 2, 
                            floorList, elevatorList, randomSeed, len(floorList), untilTime, 
                            cid_gen=cid_gen, 
                            customer_logger=customer_logger, 
                            elev_logger=elev_logger, 
                            queue_logger=queue_logger, 
                            stopList_logger=stopList_logger)
    
    log_folder = r"../data/log"
    elev_logger.to_csv (joinPath(log_folder, "elev_log.csv"))
    queue_logger.to_csv(joinPath(log_folder, "queue_log.csv"))
    stopList_logger.to_csv(joinPath(log_folder, "stopList_log.csv"))
    customer_logger.to_csv(joinPath(log_folder, "customer_log.csv"))
    
    background = dict()
    background["buildingName"] = location
    background["elevatorList"] = elevatorList
    background["floorList"] = floorList
    background["elev_infeasible"] = {elevIndex:ELEV_INFEASIBLE[elevIndex] for elevIndex in elevatorList}
    with open(joinPath(log_folder, "background.json"), 'w', encoding="utf-8") as file:
        file.write(json.dumps(background))