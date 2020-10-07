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
    

    # config parameter
    buildingName = ["Research", "NHB", "SC", "SHB"]         # usable building
    location = ["研究大樓", "北棟病床", "南棟客梯", "南棟病床"]
    untilTime = 1000
    path = '../data/BestFitDistribution.csv'
    IAT_D_section = 2 # inter-arrival time, time section
    logging.basicConfig(level=logging.CRITICAL)

    
    for buildingI in range(1): # every building
        for subElevNum in [2]: #range(2, len(ELEVATOR_GROUP[location[buildingI]])) : # subgroup elevator num pair
            for eleSepFloor in ["7"]: #BUILDING_FLOOR[location[buildingI]][1:len(BUILDING_FLOOR[location[buildingI]])]: # seperate floor using every floor
                df = []
                ele_df = []
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

                    # elevator log
                    print(type(elev_logger))

                    ele_log_result = elev_logger.df
                    ele_result_floor = ele_log_result.loc[ele_log_result["action"]==1]
                    ele_result_stop = ele_log_result.loc[ele_log_result["action"]==0]


                    floor_count = ele_result_floor.groupby('name')
                    stop_count = ele_result_floor.groupby('name')

                    for name, ele in floor_count:
                        count = ele["action"].count()
                        ele_df.append({
                                'location': location[buildingI]
                                ,'elevator_subgroup_number': [subElevNum,len(ELEVATOR_GROUP[location[buildingI]])-subElevNum]
                                ,'policy_middle_floor':eleSepFloor
                                ,'elevator name': name
                                ,'count type': "count floor"
                                ,'floor count':count
                        })
                    for name, ele in stop_count:
                        count = ele["action"].count()
                        ele_df.append({
                                'location': location[buildingI]
                                ,'elevator_subgroup_number': [subElevNum,len(ELEVATOR_GROUP[location[buildingI]])-subElevNum]
                                ,'policy_middle_floor':eleSepFloor
                                ,'elevator name': name
                                ,'count type': "count stop"
                                ,'stop': count
                        })

                    ele_log_result = pd.DataFrame(ele_log_result)
                    ele_log_result.to_csv('../data/ele_logger.csv', mode = 'a', header = False)
                    # new result

                    # new_result = customer_logger.df
                    # # waiting time & journey time
                    # new_result = new_result.loc[new_result['pass_by'][-1]==str(new_result['destination'])]
                    # df.append({
                    #     'location': location[buildingI]
                    #     ,'elevator_subgroup_number': [subElevNum,len(ELEVATOR_GROUP[location[buildingI]])-subElevNum]
                    #     ,'policy_middle_floor':eleSepFloor
                    #     ,'TimeType':'waiting_time'
                    #     ,'Time': new_result['total_waiting_time'].mean()
                    # })
                    # df.append({
                    #     'location': location[buildingI]
                    #     ,'elevator_subgroup_number': [subElevNum,len(ELEVATOR_GROUP[location[buildingI]])-subElevNum]
                    #     ,'policy_middle_floor':eleSepFloor
                    #     ,'TimeType':'journey_time'
                    #     ,'Time': new_result['total_journey_time'].mean()
                    # })

                    # end new result

                ele_df = pd.DataFrame(ele_df)
                df = pd.DataFrame(df)
                df.to_csv('../data/simulation_multipleTimes.csv', mode = 'a', header = False)
                ele_df.to_csv('../data/floor_count.csv', mode = 'a', header = False)
    statistic_df = pd.read_csv('../data/simulation_multipleTimes.csv',names=['location', 'elevator_subgroup_number', 'policy_middle_floor', 'TimeType', 'Time'])
    statistic_df.to_csv('../data/simulation_multipleTimes.csv')
    
           