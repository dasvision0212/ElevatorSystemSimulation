import simpy
import random
import pandas as pd
import sys
sys.path.append('../')

from elev_sim import *
from elev_sim.conf.NTU_hospital_conf import ELEVATOR_GROUP
import logging

# !!! ISSUE: we should consider the situation where the size of log is zero. On that situation, we could not do any operation on it. 

# check timeSection
def runElevatorSimulation(env, Dist_InterArrival, Ratio_byFloor, location, timeSection, floorList, elevatorList,
                          randomSeed, floorNum, untilTime, event:Event, cid_gen=None, 
                          customer_logger:Customer_logger=None, elev_logger:Elev_logger=None):
    random.seed(randomSeed)
    IAT_D = IAT_Distribution(Dist_InterArrival)
    DD = pd.read_csv(Ratio_byFloor).iloc[:, 1:].set_index(
        'from').iloc[0:floorNum+1, 0:floorNum+1]
    DD = DD.drop(['B2'], axis=1).drop(['B2'], axis=0) # !!!!!! not reusable

    # process
    floors_upward = [Floor(env, floorName,  1, IAT_D.getter(location, timeSection, 'up', floorName), 
                            DD.loc[floorName][floorName.lstrip("0"):], cid_gen, event) for floorName in floorList[:-1]]
    floors_downward = [Floor(env, floorName, -1, IAT_D.getter(location, timeSection, 'down', floorName), 
                            DD.loc[floorName][:floorName.lstrip("0")], cid_gen, event) for floorName in floorList[1:]]
    elevator_ctrl = ElevatorController(env, elevatorList, floorList, event, customer_logger)
    env.run(until=untilTime)


if(__name__ == "__main__"):
    logging.basicConfig(level=logging.DEBUG)
    untilTime = 1000

    Dist_InterArrival = '../data/BestFitDistribution.csv'
    timeSection = 2
    floorList = ['B4', 'B3', 'B1', '1', '2', '3', '4', '5',
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
                    event = Event(env, floorList, elevatorList)
                    customer_logger = Customer_logger(status=True)
                    elev_logger = Elev_logger(status=True)

                    runElevatorSimulation(env, Dist_InterArrival, Ratio_byFloor[locationI], location[locationI], 2, 
                                          floorList[:floorNum], elevatorList[:eleNum], randomSeed, floorNum, untilTime, 
                                          event, cid_gen, customer_logger, elev_logger)

                    result = customer_logger.df
                    meanStatistic_EleNum.append({
                        'location': location[locationI], 
                        'floorNum': floorNum, 'Elevator Amount': eleNum+1,
                        'waiting_Time': result['waiting_time'].mean(),
                        'journey_Time': result['journey_time'].mean()})

            meanStatistic_EleNum = pd.DataFrame(meanStatistic_EleNum)
            Statistic_df.append({
                'location': location[locationI],
                'elevator Amount': eleNum+1,
                'waiting_Time': meanStatistic_EleNum['waiting_Time'].mean(), 
                'journey_Time': meanStatistic_EleNum['journey_Time'].mean()})
                
        Statistic_df = pd.DataFrame(Statistic_df)
        print(Statistic_df)
