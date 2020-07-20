import simpy
import numpy.random as random
import pandas as pd
import sys
sys.path.append('../')

from elev_sim import *
from elev_sim.conf.NTUH_conf import ELEVATOR_GROUP, BUILDING_FLOOR
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
        elevatorList = ELEVATOR_GROUP[location]
        floorList    = BUILDING_FLOOR[location]
        for eleNum in range(1, 6):
            meanStatistic_EleNum = []
            for floorNum in [5, len(floorList)]:
                for j in range(100):
                    randomSeed = int(random.rand(1)*10000)
                    # Enviornment Variable
                    env = simpy.Environment()
                    cid_gen = cid_generator()

                    # Global
                    customer_logger = Customer_logger(status=True)
                    elev_logger = Elev_logger(status=True)
                    queue_logger = Queue_logger(status=True)

                    runElevatorSimulation(env, Dist_InterArrival, Ratio_byFloor[location], location, 2, 
                                          floorList[:floorNum], elevatorList[:eleNum], randomSeed, floorNum, untilTime, 
                                          cid_gen=cid_gen, 
                                          customer_logger=customer_logger, elev_logger=elev_logger, queue_logger=queue_logger)

                    result = customer_logger.df
                    meanStatistic_EleNum.append({
                        'location': location, 
                        'floorNum': floorNum, 'Elevator Amount': eleNum+1,
                        'waiting_Time': result['waiting_time'].mean(),
                        'journey_Time': result['journey_time'].mean()})

                    # used for animation
                    elev_logger.to_csv(r"../data/elevator_log.csv")
                    queue_logger.to_csv(r"../data/queue_log.csv")

            meanStatistic_EleNum = pd.DataFrame(meanStatistic_EleNum)
            Statistic_df.append({
                'location': location,
                'elevator Amount': eleNum+1,
                'waiting_Time': meanStatistic_EleNum['waiting_Time'].mean(), 
                'journey_Time': meanStatistic_EleNum['journey_Time'].mean()})
                
        Statistic_df = pd.DataFrame(Statistic_df)
