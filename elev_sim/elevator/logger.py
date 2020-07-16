import pandas as pd
from elev_sim.conf.log_conf import ELEVLOG_CONFIG, QUEUE_LOG_CONFIG

class Logger:
    def __init__(self, status=False):
        self.status = status
        self._log = list()
        self._df = None

    @property
    def df(self):
        if(self._df == None):
            self._df = pd.DataFrame(self._log)
        elif(self._df.shape[0] != len(self._log) or len(self._log) == 0):
            self._df = pd.DataFrame(self._log)

        return self._df

    def to_csv(self, export_path, preserveIndex=False):
        self.df.to_csv(export_path, index=preserveIndex)


class Elev_logger(Logger):
    def __init__(self, status):
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
    def __init__(self, status):
        super().__init__(status)
    
    def log(self, customer):
        if(not self.status):
            return

        self._log.append(vars(customer))

    @property
    def df(self):
        super().df

        if(self._df.shape[0] != 0):
            self._df['waiting_time'] = self._df['boarding_time'] - self._df['start_time']
            self._df['journey_time'] = self._df['leave_time'] - self._df['start_time']
        
        return self._df


class Queue_logger(Logger):
    def __init__(self, status):
        super().__init__(status)

    def log_inflow(self, riderNumAfter, floorIndex, direction, time):
        self._log.append({
            'action'       : QUEUE_LOG_CONFIG.INFLOW,
            'riderNumAfter': riderNumAfter,
            "floorIndex"   : floorIndex, 
            "direction"    : direction, 
            "time"         : time
        })

    def log_outflow(self, riderNumAfter, floorIndex, direction, time):
        self._log.append({
            'action'       : QUEUE_LOG_CONFIG.OUTFLOW,
            'riderNumAfter': riderNumAfter,
            "floorIndex"   : floorIndex, 
            "direction"    : direction, 
            "time"         : time
        })
    