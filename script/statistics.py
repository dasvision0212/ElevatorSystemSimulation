#!/usr/bin/python
# -*- coding: utf-8 -*-

import simpy
import numpy.random as random
import pandas as pd
import sys, os
sys.path.append('../')

from elev_sys import *
from elev_sys.conf.NTUH_conf import ELEVATOR_GROUP, BUILDING_FLOOR
from elev_sys.simulation.path_finder import Path_finder
import logging

# !!! ISSUE: we should consider the situation where the size of log is zero. On that situation, we could not do any operation on it. 

if(__name__ == "__main__"):
    

    # config parameter
    buildingName = ["Research", "NHB", "SC", "SHB"]      # usable building
    location = ["研究大樓", "北棟病床", "南棟客梯", "南棟病床"]
    untilTime = 14400
    path = '../data/BestFitDistribution.csv'
    IAT_D_section = 2                                    # inter-arrival time, time section
    logging.basicConfig(level=logging.CRITICAL)
    

    group_setting = {
        'a': {
            'available_floor': [
                ["B4", "B3", "B2", "B1", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"],
                ["B4", "B3", "B2", "B1", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"],
                ["B4", "B3", "B2", "B1", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"]
            ],
        }
    }

    if os.path.exists("../data/simulation_multipleTimes.csv"):
        os.remove("../data/simulation_multipleTimes.csv")

    for buildingI in range(1):                          # every building

        # setting parameter
        building_name = location[buildingI]
        floorList = BUILDING_FLOOR[building_name]
        IAT_D = IAT_Distribution(path, building_name, IAT_D_section)
        distination_dist = pd.read_csv('../data/FloorRatio_'+buildingName[0]+'.csv').iloc[:, 1:].set_index(
                    'from').iloc[0:len(floorList)+1, 0:len(floorList)+1]

        # for sep in range(1, len(floorList)-1):            # generate policy
        #     group_setting['a']['available_floor'] = []
        #     if(sep < floorList.index("1")):
        #         temp = floorList[:sep+1].copy()
        #         temp.append("1")
        #         group_setting['a']['available_floor'].append(temp)
        #         group_setting['a']['available_floor'].append(floorList[sep+1:])
        #     elif(i == floorList.index("1")):
        #         group_setting['a']['available_floor'].append(floorList[:sep+1])
        #         group_setting['a']['available_floor'].append(floorList[sep+1:])
        #     else:
        #         temp = floorList[sep+1:].copy()
        #         temp.insert(0,"1")
        #         group_setting['a']['available_floor'].append(floorList[:sep+1])
        #         group_setting['a']['available_floor'].append(temp)

        df = []                                     # output statistic

        path_finder = Path_finder(floorList, group_setting, fileName="path_log.json")
        for i in range(100):                          # times of simulation
        
            # setting parameter
            randomSeed = int(random.rand(1)*10000)
            env = simpy.Environment()
            cid_gen = cid_generator()

            # Global
            customer_logger = Customer_logger(untilTime, status=True)
            elev_logger = Elev_logger(status=True)
            queue_logger = Queue_logger(status=True)
            stopList_logger = StopList_logger(status=True)

            returnStatistic = runElevatorSimulation(env, IAT_D, distination_dist, floorList, group_setting, 
                                                    randomSeed, path_finder,2500, 
                                                    cid_gen=cid_gen,
                                                    customer_logger=customer_logger,
                                                    elev_logger=elev_logger,
                                                    queue_logger=queue_logger,
                                                    stopList_logger=stopList_logger)

            result = customer_logger.df
            
            # waiting & journey time df recording
            df.append({
                    'location': building_name
                    ,'sep_floor': 'odd-even-division'
                    ,'dataType':'waiting_time'
                    ,'data': result['total_waiting_time'].mean()
            })
            df.append({
                    'location': building_name
                    ,'sep_floor': 'odd-even-division'
                    ,'dataType':'journey_time'
                    ,'data': result['journey_time'].mean()
            })

            # elevator stop & floor_count df recording
            ele_log_result = elev_logger.df
            ele_result_floor = ele_log_result.loc[ele_log_result["action"]==1]
            ele_result_stop = ele_log_result.loc[ele_log_result["action"]==0]

            df.append({
                    'location': building_name
                    ,'sep_floor': 'odd-even-division'
                    ,'dataType': "count_floor"
                    ,'data':len(ele_result_floor)
            })
            df.append({
                    'location': building_name
                    ,'sep_floor': 'odd-even-division'
                    ,'dataType': "count_stop"
                    ,'data': len(ele_result_stop)
            })


            # ineffective door open
            df.append({
                    'location': building_name
                    ,'sep_floor': 'odd-even-division'
                    ,'dataType': "count_wasted"
                    ,'data': returnStatistic['waste_stop_num'].sum()
            })

                # output n times record in one policy at once
        df = pd.DataFrame(df)
        df.reset_index(drop=True)
        df.to_csv('../data/simulation_multipleTimes.csv', mode = 'a', header = False)

    # add header & output
    statistic_df = pd.read_csv('../data/simulation_multipleTimes.csv',names=['location',  'sep_floor', 'dataType', 'data'])
    statistic_df.to_csv('../data/simulation_multipleTimes.csv')