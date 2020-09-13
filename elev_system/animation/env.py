from elev_system.conf.animation_conf import DEFAULT_ANIMA_CONFIG


class Env:
    def __init__(self, speed=DEFAULT_ANIMA_CONFIG.SPEED):
        self.now = [0]
        self.speed = speed
        self.status = False # True denotes running, False denotes pausing

        
    def delay_by_time(self, time, now:list):
        period = time-now[0]
        if(period <= 0):
            return 0
        else:
            return int(period * 1000/self.speed) # should be transfer into ms

    def delay_by_interval(self, time):
        return int(time * 1000/self.speed) # should be transfer into ms