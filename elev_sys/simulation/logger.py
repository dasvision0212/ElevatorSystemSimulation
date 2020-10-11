import pandas as pd
from collections import defaultdict
from elev_sys.conf.log_conf import ELEVLOG_CONFIG, QUEUE_LOG_CONFIG, STOPLIST_LOG_CONFIG


class Logger:
    def __init__(self, status=True):
        self.status = status
        self._log = list()
        self._df = None

    @property
    def df(self):
        if(self._df is None):
            self._df = pd.DataFrame(self._log)
        elif(self._df.shape[0] != len(self._log) or len(self._log) == 0):
            self._df = pd.DataFrame(self._log)
        
        return self._df

    @df.setter
    def df(self, num):
        if(hasattr(self, "_df")):
            raise AttributeValue("[!] Can't change the log. ")
        self._df = num

    def to_csv(self, export_path, preserveIndex=False):
        self.df.to_csv(export_path, index=preserveIndex)


class Elev_logger(Logger):
    def __init__(self, status=True):
        super().__init__(status)
    
    def log_arrive(self, elev_name, direction, floor, time):
        if(not self.status):
            return
        
        self._log.append({
            'name'     : elev_name,
            'direction': direction,
            'action'   : ELEVLOG_CONFIG.ARRIVE,
            'floor'    : floor,
            'time'     : time
            })

    def log_idle(self, elev_name, floor, time):
        if(not self.status):
            return
        
        self._log.append({
            'name'  : elev_name,
            'action': ELEVLOG_CONFIG.IDLE,
            'floor' : floor,
            'time'  : time
            })

    def log_serve(self, elev_name, riderNumAfter, direction, floor, time):
        if(not self.status):
            return
        
        self._log.append({
            'name'         : elev_name, 
            'action'       : ELEVLOG_CONFIG.SERVE,
            'riderNumAfter': riderNumAfter,
            'floor'        : floor,
            'direction'    : direction,
            'time'         : time
        })


class Customer_logger(Logger):
    def __init__(self, untilTime, status=True):
        super().__init__(status)
        self.untilTime = untilTime
    
    def log_appear(self, cid:int, source:str, distination, time:float):
        if(not self.status):
            return

        self._log.append(defaultdict(list, {
            "cid": cid,
            "pass_by": [source], 
            "appear_time": time, 
            "destination": distination
        }))

    def log_board(self, cid, time:float):
        if(not self.status):
            return

        customer = self._log[cid]
        customer["boarding_time"].append(time)

    def log_get_off(self, cid, floor, time ):
        if(not self.status):
            return

        customer = self._log[cid]
        customer["pass_by"].append(floor)
        customer["get_off_time"].append(time)

    @property
    def df(self):
        # build self._df
        if(self._df is None):
            self._df = pd.DataFrame(self._log)
        elif(self._df.shape[0] != len(self._log) or len(self._log) == 0):
            self._df = pd.DataFrame(self._log)
        
        # check if the total_waiting_time and total_journey_time has been calculated
        if("total_waiting_time" in self._df.columns):
            return self._df

        # calculate total_waiting_time and total_journey_time
        waiting_time_list = list()
        time_in_elev_list = list()
        transfer_num_list = list()
        isSuccessful_list = list()
        for i, row in self._df.iterrows():
            if(row["pass_by"][-1] == row["destination"]):
                transfer_num_list.append(len(row["pass_by"])-2)
                isSuccessful_list.append(True)
            else:
                transfer_num_list.append(len(row["pass_by"])-1)
                isSuccessful_list.append(False)
                

            # deal with exception
            if(not isinstance(row["boarding_time"], list)): 
                '''
                Check if row["boarding_time"] not pd.na. 
                We cannot apply pd.isnull or pd.isna because it will return a list, e.g., [True, False]. 
                It is not out expectation. What we want is that the cell row["boarding_time"] is pd.nan or not. 
                '''
                waiting_time_list.append(self.untilTime - row["appear_time"])
                time_in_elev_list.append(pd.NA)
                continue

            if(not isinstance(row["get_off_time"], list)):
                waiting_time_list.append(row["boarding_time"][0] - row["appear_time"])
                time_in_elev_list.append(self.untilTime - row["boarding_time"][0])
                continue

            # get total_waiting_time
            total_waiting_time = 0
            for boarding_i, boarding_time in enumerate(row["boarding_time"]):        
                if(not boarding_i):
                    total_waiting_time += boarding_time - row["appear_time"]
                else:
                    total_waiting_time += boarding_time - row["get_off_time"][boarding_i-1]

            # get total_journey_time
            total_journey_time = 0
            for get_off_i, get_off_time in enumerate(row["get_off_time"]):
                total_journey_time += get_off_time - row["boarding_time"][get_off_i]

            if(len(row["boarding_time"]) == len(row["get_off_time"])):
                if(row["pass_by"][-1] != row["destination"]):
                    total_waiting_time += self.untilTime - row["get_off_time"][-1]
            else:
                total_journey_time += self.untilTime - row["boarding_time"][-1]

            waiting_time_list.append(total_waiting_time)
            time_in_elev_list.append(total_journey_time)

        self._df["total_waiting_time"] = waiting_time_list
        self._df["time_in_elev"]       = time_in_elev_list
        self._df["journey_time"]       = self._df["total_waiting_time"] + self._df["time_in_elev"]
        self._df["transfer_num"]       = transfer_num_list
        self._df["isSuccessful"]       = isSuccessful_list

        return self._df


class Queue_logger(Logger):
    def __init__(self, status=True):
        super().__init__(status)

    def log_inflow(self, riderNumAfter, floorIndex, direction, time):
        if(not self.status):
            return

        self._log.append({
            'action'       : QUEUE_LOG_CONFIG.INFLOW,
            'riderNumAfter': riderNumAfter,
            "floorIndex"   : floorIndex, 
            "direction"    : direction, 
            "time"         : time
        })

    def log_outflow(self, riderNumAfter, floorIndex, direction, time):
        if(not self.status):
            return

        self._log.append({
            'action'       : QUEUE_LOG_CONFIG.OUTFLOW,
            'riderNumAfter': riderNumAfter,
            "floorIndex"   : floorIndex, 
            "direction"    : direction, 
            "time"         : time
        })
    

class StopList_logger(Logger):
    def __init__(self, status=True):
        super().__init__(status)

    def log_active(self, elevIndex, direction, floorIndex, time):
        if(not self.status):
            return

        self._log.append({
            "elevIndex"    : elevIndex, 
            "direction"    : direction, 
            "floorIndex"   : floorIndex, 
            'latterStatus' : STOPLIST_LOG_CONFIG.ACTIVE,
            "time"         : time
        })

    def log_idle(self, elevIndex, direction, floorIndex, time):
        if(not self.status):
            return

        self._log.append({
            "elevIndex"    : elevIndex, 
            "direction"    : direction, 
            "floorIndex"   : floorIndex, 
            'latterStatus' : STOPLIST_LOG_CONFIG.IDLE,
            "time"         : time
        })