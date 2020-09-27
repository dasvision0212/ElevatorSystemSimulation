import simpy
import numpy.random as random
import pandas as pd
import sys
sys.path.append('../')

from elev_sys import *
from elev_sys.conf.NTUH_conf import ELEVATOR_GROUP, BUILDING_FLOOR
import logging

# !!! ISSUE: we should consider the situation where the size of log is zero. On that situation, we could not do any operation on it. 

if(__name__ == "__main__"):
    logging.basicConfig(level=logging.WARNING)
    untilTime = 1000

    Dist_InterArrival = '../data/BestFitDistribution.csv'
    timeSection = 2
    
    # Variable
    Ratio_byFloor = {"北棟病床": '../data/FloorRatio_NHB.csv',
                     "研究大樓": '../data/FloorRatio_Research.csv',
                     "南棟客梯": '../data/FloorRatio_SC.csv' , 
                     "南棟病床": '../data/FloorRatio_SHB.csv'}

    location = ["北棟病床", "研究大樓", "南棟客梯", "南棟病床"]

    for location in location[:4]:
        Statistic_df = []
        elevNameList = ELEVATOR_GROUP[location]
        floorList    = BUILDING_FLOOR[location]
        for eleNum in range(1, len(elevNameList)):
            for floorNum in [len(floorList)]: # !!! if you adjust the number of floor, you should simultaneously update IAT
                df = []
                for j in range(100):
                    # Enviornment Variable
                    env = simpy.Environment()
                    cid_gen = cid_generator()
                    randomSeed = int(random.rand(1)*10000)
                    
                    # Global
                    customer_logger = Customer_logger(status=True)
                    elev_logger = Elev_logger(status=True)
                    queue_logger = Queue_logger(status=True)

                    runElevatorSimulation(env, Dist_InterArrival, Ratio_byFloor[location], location, 2, 
                                          floorList[:floorNum], elevNameList[:eleNum], randomSeed, floorNum, untilTime, 
                                          cid_gen=cid_gen, 
                                          customer_logger=customer_logger, elev_logger=elev_logger, queue_logger=queue_logger)

                    result = customer_logger.df
                    df.append({
                        'location': location
                        ,'floorNum': floorNum
                        ,'version':3 
                        ,'Elevator Amount': eleNum+1
                        ,'TimeType':'waiting_time'
                        ,'Time': result['waiting_time'].mean()})
                    df.append({
                        'location': location
                        ,'floorNum': floorNum
                        ,'version':3 
                        ,'Elevator Amount': eleNum+1
                        ,'TimeType':'journey_Time'
                        ,'Time': result['journey_time'].mean()})
                    

                    # used for animation
                    # elev_logger.to_csv(r"../data/elevator_log.csv")
                    # queue_logger.to_csv(r"../data/queue_log.csv")

                df = pd.DataFrame(df)
                df.to_csv('../data/tryData.csv', mode = 'a', header = False, index= False)
        print('finish', location)


