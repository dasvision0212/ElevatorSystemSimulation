from os.path import join as joinPath
import logging
import sys
sys.path.append('../')

from elev_sys.conf.NTUH_conf import ELEVATOR_GROUP, BUILDING_FLOOR
from elev_sys.simulation.IAT_Distribution import IAT_Distribution
from elev_sys import *
import simpy
import pandas as pd
import json


if(__name__ == "__main__"):

    # simulation related
    logging.basicConfig(level=logging.CRITICAL)
    untilTime = 3600 * 4

    # env variable
    Ratio_byFloor = {"北棟病床": '../data/FloorRatio_NHB.csv',
                     "研究大樓": '../data/FloorRatio_Research.csv',
                     "南棟客梯": '../data/FloorRatio_SC.csv',
                     "南棟病床": '../data/FloorRatio_SHB.csv'}

    location = ["北棟病床", "研究大樓", "南棟客梯", "南棟病床"][0]
    timeSection = 2
    floorList = BUILDING_FLOOR[location]

    # distribution
    Dist_InterArrival_file = '../data/BestFitDistribution.csv'
    IAT_D = IAT_Distribution(Dist_InterArrival_file, location, timeSection)
    distination_dist = pd.read_csv(Ratio_byFloor[location]).iloc[:, 1:].set_index(
        'from').iloc[0:len(floorList)+1, 0:len(floorList)+1]
    distination_dist = distination_dist.drop(['B2'], axis=1).drop(['B2'], axis=0)

    # sub_group_setting
    group_setting = {
        'a': {
            'available_floor': [
                ['B4', 'B3', 'B1','1'], 
                ['1', '2', '3', '4', '5'],
                ['5', '6', '7', '8', '11', '12', '13', '14', '15'], 
                ['B3', 'B2'],
                ['8', '9', '10', '11']
            ],
        }
    }
    
    # Enviornment Variable
    env = simpy.Environment()
    cid_gen = cid_generator()
    randomSeed = 1234

    # Define Logger
    customer_logger = Customer_logger(untilTime, status=True)
    elev_logger = Elev_logger(status=True)
    queue_logger = Queue_logger(status=True)
    stopList_logger = StopList_logger(status=True)

    # Simulation
    statistics = runElevatorSimulation(env, IAT_D, distination_dist, floorList, group_setting, randomSeed, 14000,
                          cid_gen=cid_gen,
                          customer_logger=customer_logger,
                          elev_logger=elev_logger,
                          queue_logger=queue_logger,
                          stopList_logger=stopList_logger)


    # logging
    log_folder = r"../data/log2"
    try:
        elev_logger.to_csv(joinPath(log_folder, "elev_log.csv"))
    except PermissionError as e:
        raise e
    
    try:
        queue_logger.to_csv(joinPath(log_folder, "queue_log.csv"))
    except PermissionError:
        pass

    try:
        stopList_logger.to_csv(joinPath(log_folder, "stopList_log.csv"))
    except PermissionError:
        pass

    try:
        customer_logger.to_csv(joinPath(log_folder, "customer_log.csv"))
    except PermissionError:
        pass

    background = dict()
    background["buildingName"] = location
    background["floorList"] = floorList
    background["sub_group_setting"] = group_setting

    # 過渡期
    group_name = list(group_setting.keys())[0]
    background["elev_available_floor"] = {group_name+str(i):available_floor for i, available_floor in \
                                          enumerate(group_setting[group_name]["available_floor"])}
    background["elevatorList"] = [group_name+str(i) for i in range(len(group_setting[group_name]["available_floor"]))]
    background["sub_group_setting"] = group_setting
    with open(joinPath(log_folder, "background.json"), 'w', encoding="utf-8") as file:
        json.dump(background, file, ensure_ascii=False)

    # statistics records stop_num and move_floor_num
    print(statistics)