import pandas as pd

from elev_sys.simulation.sub_group import SubGroup
from elev_sys.simulation.logger import (Customer_logger, Elev_logger, StopList_logger)

class Elevator_group:
    def __init__(self, env, group_setting, floorList, event, 
                customer_logger:Customer_logger=None, elev_logger:Elev_logger=None, stopList_logger:StopList_logger=None):
        
        self.env = env
        self.sub_group = {}
        for sub_group_name, sub_group_setting in group_setting.items():
            self.sub_group[sub_group_name] = SubGroup(env, floorList, sub_group_name, sub_group_setting, event, 
                                       customer_logger=customer_logger, 
                                       elev_logger=elev_logger, 
                                       stopList_logger=stopList_logger)

    def get_statistics(self):
        statistics = pd.DataFrame()
        for sub_group in self.sub_group.values():
            statistics = pd.concat([statistics, sub_group.get_statistics()], axis=0)

        return statistics 