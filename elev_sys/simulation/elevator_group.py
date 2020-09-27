from elev_sys.simulation.sub_group import SubGroup
from elev_sys.simulation.logger import (Customer_logger, Elev_logger, StopList_logger)

class Elevator_group:
    def __init__(self, env, sub_group_setting, floorList, event, 
                customer_logger:Customer_logger=None, elev_logger:Elev_logger=None, stopList_logger:StopList_logger=None):
        
        self.env = env
        self.sub_group = {}
        for groupName, setting in sub_group_setting.items():
            self.sub_group[groupName] = SubGroup(env, floorList, (groupName, setting), event, 
                                       customer_logger=customer_logger, 
                                       elev_logger=elev_logger, 
                                       stopList_logger=stopList_logger)