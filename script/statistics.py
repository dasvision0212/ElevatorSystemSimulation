import simpy
import random
import pandas as pd
import sys
sys.path.append('../')

from elev_sim import *
from elev_sim.conf.NTU_hospital_conf import ELEVATOR_GROUP
import logging

# !!! ISSUE: we should consider the situation where the size of log is zero. On that situation, we could not do any operation on it. 

if(__name__ == "__main__"):
    logging.basicConfig(level=logging.WARNING)
    untilTime = 1000

    Dist_InterArrival = '../data/BestFitDistribution.csv'
    timeSection = 2
    
    floorList = ['B4', 'B3', 'B2', 'B1', '1', '2', '3', '4', '5',
                 '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']

    # Variable
    Ratio_byFloor = ['../data/FloorRatio_NHB.csv', '../data/FloorRatio_Research.csv',
                     '../data/FloorRatio_SC.csv' , '../data/FloorRatio_SHB.csv']

    location = ["北棟病床", "研究大樓", "南棟客梯", "南棟病床"]

    # elevatorGroup
    elevatorList = ELEVATOR_GROUP["北棟客梯"]

    for locationI in range(len(location[:1])):
        Statistic_df = []
        for eleNum in [len(elevatorList)]:
            meanStatistic_EleNum = []
            for floorNum in [len(floorList)]:
                for j in range(1):
                    randomSeed = 1234
                    # Enviornment Variable
                    env = simpy.Environment()
                    cid_gen = cid_generator()

                    # Global Event
                    customer_logger = Customer_logger(status=True)
                    elev_logger = Elev_logger(status=True)
                    queue_logger = Queue_logger(status=True)

                    runElevatorSimulation(env, Dist_InterArrival, Ratio_byFloor[locationI], location[locationI], 2, 
                                          floorList[:floorNum], elevatorList[:eleNum], randomSeed, floorNum, untilTime, 
                                          cid_gen=cid_gen, 
                                          customer_logger=customer_logger, elev_logger=elev_logger, queue_logger=queue_logger)

                    result = customer_logger.df
                    meanStatistic_EleNum.append({
                        'location': location[locationI], 
                        'floorNum': floorNum, 'Elevator Amount': eleNum+1,
                        'waiting_Time': result['waiting_time'].mean(),
                        'journey_Time': result['journey_time'].mean()})

                    # used for animation
                    elev_logger.to_csv(r"../data/elevator_log.csv")
                    queue_logger.to_csv(r"../data/queue_log.csv")

            meanStatistic_EleNum = pd.DataFrame(meanStatistic_EleNum)
            Statistic_df.append({
                'location': location[locationI],
                'elevator Amount': eleNum+1,
                'waiting_Time': meanStatistic_EleNum['waiting_Time'].mean(), 
                'journey_Time': meanStatistic_EleNum['journey_Time'].mean()})
                
        Statistic_df = pd.DataFrame(Statistic_df)
