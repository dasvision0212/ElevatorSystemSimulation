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
    untilTime = 14400
    path = '../data/BestFitDistribution.csv'
    IAT_D_section = 2 # inter-arrival time, time section
    logging.basicConfig(level=logging.CRITICAL)
    group_setting = []
    group_setting_name = ["all_feasible","sep_1_5", "sep_2_7"]
    
    group_setting.append({
        'a': {
            'infeasibles': [
                [],
                [],
                []
            ]
        }
    })
    group_setting.append({
        'a': {
            'infeasibles': [
                [ '2', '3', '4','5','6','7','8','9','10','11','12','13','14','15'],
                ['B4', 'B3', 'B2', 'B1','6','7','8','9','10', '11', '12', '13', '14', '15'],
                ['B4', 'B3', 'B2', 'B1', '1', '2', '3', '4']
            ]
        }
    })
    group_setting.append({
        'a': {
            'infeasibles': [
                [ '3', '4','5','6','7','8','9','10','11','12','13','14','15'],
                ['B4', 'B3', 'B2', 'B1','1','8','9','10', '11', '12', '13', '14', '15'],
                ['B4', 'B3', 'B2', 'B1', '1', '2', '3', '4','5','6']
            ]
        }
    })



    
    for buildingI in range(1): # every building
        for subElevNum in [2]: #range(2, len(ELEVATOR_GROUP[location[buildingI]])) : # subgroup elevator num pair
            for floor_policy in range(len(group_setting)): #BUILDING_FLOOR[location[buildingI]][1:len(BUILDING_FLOOR[location[buildingI]])]: # seperate floor using every floor
                df = []
                ele_df = []
                for i in range(100): # times of simulation
                    # setting parameter
                    randomSeed = int(random.rand(1)*10000)
                    floorList = BUILDING_FLOOR[location[buildingI]]
                    IAT_D = IAT_Distribution(path, location[buildingI], IAT_D_section)
                    distination_dist = pd.read_csv('../data/FloorRatio_'+buildingName[0]+'.csv').iloc[:, 1:].set_index(
                        'from').iloc[0:len(floorList)+1, 0:len(floorList)+1]
                    group_set = group_setting[floor_policy]
                    env = simpy.Environment()
                    cid_gen = cid_generator()

                    

                    # Global
                    customer_logger = Customer_logger(untilTime, status=True)
                    elev_logger = Elev_logger(status=True)
                    queue_logger = Queue_logger(status=True)
                    stopList_logger = StopList_logger(status=True)

                    runElevatorSimulation(env, IAT_D, distination_dist, floorList, group_set, 
                                        randomSeed, untilTime, cid_gen=cid_gen,
                                        customer_logger=customer_logger,
                                        elev_logger=elev_logger,
                                        queue_logger=queue_logger,
                                        stopList_logger=stopList_logger)

                    result = customer_logger.df

                    df.append({
                            'location': location[buildingI]
                            ,'elevator_subgroup_number': [subElevNum,len(ELEVATOR_GROUP[location[buildingI]])-subElevNum]
                            ,'floor_policy':group_setting_name[floor_policy]
                            ,'TimeType':'waiting_time'
                            ,'Time': result['total_waiting_time'].mean()
                    })
                    df.append({
                            'location': location[buildingI]
                            ,'elevator_subgroup_number': [subElevNum,len(ELEVATOR_GROUP[location[buildingI]])-subElevNum]
                            ,'floor_policy':group_setting_name[floor_policy]
                            ,'TimeType':'journey_time'
                            ,'Time': result['total_journey_time'].mean()
                    })

                    # elevator log

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
                                ,'floor_policy':group_setting_name[floor_policy]
                                ,'elevator_name': name
                                ,'count_type': "count_floor"
                                ,'floor_count':count
                        })
                    for name, ele in stop_count:
                        count = ele["action"].count()
                        ele_df.append({
                                'location': location[buildingI]
                                ,'elevator_subgroup_number': [subElevNum,len(ELEVATOR_GROUP[location[buildingI]])-subElevNum]
                                ,'floor_policy':group_setting_name[floor_policy]
                                ,'elevator_name': name
                                ,'count_type': "count_stop"
                                ,'floor_count': count
                        })

                df = pd.DataFrame(df)
                df.to_csv('../data/simulation_multipleTimes.csv', mode = 'a', header = False)
                ele_df = pd.DataFrame(ele_df)
                ele_df.to_csv('../data/floor_count.csv', mode = 'a', header = False)

    statistic_df = pd.read_csv('../data/simulation_multipleTimes.csv',names=['location', 'elevator_subgroup_number', 'floor_policy', 'TimeType', 'Time'])
    statistic_df.to_csv('../data/simulation_multipleTimes.csv')
    floor_policy_df = pd.read_csv('../data/floor_count.csv',names=['location', 'elevator_subgroup_number', 'floor_policy', 'elevator_name','count_type','floor_count'])
    floor_policy_df.to_csv('../data/floor_count.csv')
    

# floor list must contain ground floor
# for eleName, eleInfo in sub_group_setting.items():
#     bottomFloorI = floorList.index(eleInfo["infeasible"][0])
#     if "1" not in eleInfo["infeasible"]:
#         if bottomFloorI < floorList.index("1"):
#             eleInfo["infeasible"].append("1")
#         else:
#             eleInfo["infeasible"].insert(0,"1")