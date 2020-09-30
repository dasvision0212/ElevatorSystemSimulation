#!/usr/bin/python
# -*- coding: utf-8 -*-

import simpy
import numpy.random as random
import pandas as pd
import sys, os
sys.path.append('../')

from elev_sys import *
from elev_sys.conf.NTUH_conf import ELEVATOR_GROUP, BUILDING_FLOOR
import logging

# !!! ISSUE: we should consider the situation where the size of log is zero. On that situation, we could not do any operation on it. 

if(__name__ == "__main__"):
    
    ################ use updated structure simulation model -- subELevatorGroup ####################

    # config parameter
    buildingName = ["Research", "NHB", "SC", "SHB"]         # usable building
    location = ["研究大樓", "北棟病床", "南棟客梯", "南棟病床"]
    untilTime = 1000
    path = '../data/BestFitDistribution.csv'
    IAT_D_section = 2 # inter-arrival time, time section
    logging.basicConfig(level=logging.CRITICAL)

    
    for buildingI in range(len(location)): # every building
        for subElevNum in range(2, len(ELEVATOR_GROUP[location[buildingI]])) : # subgroup elevator num pair
            for eleSepFloor in BUILDING_FLOOR[location[buildingI]][1:len(BUILDING_FLOOR[location[buildingI]])]: # seperate floor using every floor
                df = []
                for i in range(100): # times of simulation
                    # setting parameter
                    randomSeed = int(random.rand(1)*10000)
                    floorList = BUILDING_FLOOR[location[buildingI]]
                    IAT_D = IAT_Distribution(path, location[buildingI], IAT_D_section)
                    distination_dist = pd.read_csv('../data/FloorRatio_'+buildingName[0]+'.csv').iloc[:, 1:].set_index(
                        'from').iloc[0:len(floorList)+1, 0:len(floorList)+1]
                    eleSepFloorI = floorList.index(eleSepFloor)
                    sub_group_setting = {
                                            'a':{'infeasible':floorList[:eleSepFloorI+1],'elevNum':subElevNum},
                                            'b':{'infeasible':floorList[eleSepFloorI:],'elevNum':len(ELEVATOR_GROUP[location[buildingI]])-subElevNum}
                                        }
                    env = simpy.Environment()
                    cid_gen = cid_generator()

                    # floor list must contain ground floor
                    for eleName, eleInfo in sub_group_setting.items():
                        bottomFloorI = floorList.index(eleInfo["infeasible"][0])
                        if "1" not in eleInfo["infeasible"]:
                            if bottomFloorI < floorList.index("1"):
                                eleInfo["infeasible"].append("1")
                            else:
                                eleInfo["infeasible"].insert(0,"1")

                    # Global
                    customer_logger = Customer_logger(status=True)
                    elev_logger = Elev_logger(status=True)
                    queue_logger = Queue_logger(status=True)
                    stopList_logger = StopList_logger(status=True)

                    runElevatorSimulation(env, IAT_D, distination_dist, floorList, sub_group_setting, 
                                        randomSeed, untilTime, cid_gen, 
                                        customer_logger, elev_logger, queue_logger, stopList_logger)

                    result = customer_logger.df

                    df.append({
                            'location': location[buildingI]
                            ,'elevator_subgroup_number': [subElevNum,len(ELEVATOR_GROUP[location[buildingI]])-subElevNum]
                            ,'policy_middle_floor':eleSepFloor
                            ,'TimeType':'waiting_time'
                            ,'Time': result['waiting_time'].mean()
                    })
                    df.append({
                            'location': location[buildingI]
                            ,'elevator_subgroup_number': [subElevNum,len(ELEVATOR_GROUP[location[buildingI]])-subElevNum]
                            ,'policy_middle_floor':eleSepFloor
                            ,'TimeType':'journey_time'
                            ,'Time': result['journey_time'].mean()
                    })
                df = pd.DataFrame(df)
                df.to_csv('../data/simulation_multipleTimes.csv', mode = 'a', header = False)
    statistic_df = pd.read_csv('../data/simulation_multipleTimes.csv',names=['location', 'elevator_subgroup_number', 'policy_middle_floor', 'TimeType', 'Time'])
    statistic_df.to_csv('../data/simulation_multipleTimes.csv')
    
                # pd.set_option('display.max_colwidth', -1)
                # print(result)
                # print("column: ", result.column)
    
    ################ initial simulation model ####################

    # logging.basicConfig(level=logging.WARNING)
    # untilTime = 1000

    # Dist_InterArrival = '../data/BestFitDistribution.csv'
    # timeSection = 2
    
    # # Variable
    # Ratio_byFloor = {"北棟病床": '../data/FloorRatio_NHB.csv',
    #                  "研究大樓": '../data/FloorRatio_Research.csv',
    #                  "南棟客梯": '../data/FloorRatio_SC.csv' , 
    #                  "南棟病床": '../data/FloorRatio_SHB.csv'}

    # location = ["北棟病床", "研究大樓", "南棟客梯", "南棟病床"]
    # for location in location[:4]:
    #     Statistic_df = []
    #     elevNameList = ELEVATOR_GROUP[location]
    #     floorList    = BUILDING_FLOOR[location]
    #     for eleNum in range(1, len(elevNameList)):
    #         for floorNum in [len(floorList)]: # !!! if you adjust the number of floor, you should simultaneously update IAT
    #             df = []
    #             for j in range(100):
    #                 # Enviornment Variable
    #                 env = simpy.Environment()
    #                 cid_gen = cid_generator()
    #                 randomSeed = int(random.rand(1)*10000)
                    
    #                 # Global
    #                 customer_logger = Customer_logger(status=True)
    #                 elev_logger = Elev_logger(status=True)
    #                 queue_logger = Queue_logger(status=True)

    #                 runElevatorSimulation(env, Dist_InterArrival, Ratio_byFloor[location], location, 2, 
    #                                       floorList[:floorNum], elevNameList[:eleNum], randomSeed, floorNum, untilTime, 
    #                                       cid_gen=cid_gen, 
    #                                       customer_logger=customer_logger, elev_logger=elev_logger, queue_logger=queue_logger)

    #                 result = customer_logger.df
    #                 df.append({
    #                     'location': location
    #                     ,'floorNum': floorNum
    #                     ,'version':3 
    #                     ,'Elevator Amount': eleNum+1
    #                     ,'TimeType':'waiting_time'
    #                     ,'Time': result['waiting_time'].mean()})
    #                 df.append({
    #                     'location': location
    #                     ,'floorNum': floorNum
    #                     ,'version':3 
    #                     ,'Elevator Amount': eleNum+1
    #                     ,'TimeType':'journey_Time'
    #                     ,'Time': result['journey_time'].mean()})
                    

    #                 # used for animation
    #                 # elev_logger.to_csv(r"../data/elevator_log.csv")
    #                 # queue_logger.to_csv(r"../data/queue_log.csv")

    #             df = pd.DataFrame(df)
    #             df.to_csv('../data/tryData.csv', mode = 'a', header = False, index= False)
    #     print('finish', location)


