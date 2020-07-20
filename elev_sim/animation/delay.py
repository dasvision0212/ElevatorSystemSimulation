from elev_sim.conf.animation_conf import DEFAULT_ANIMA_CONFIG


def delay_by_time(time, now:list, speed=DEFAULT_ANIMA_CONFIG.SPEED):
    period = time-now[0]
    if(period <= 0):
        return 0
    else:
        return int(period * 1000/speed) # should be transfer into ms

def delay_by_interval(time, speed=DEFAULT_ANIMA_CONFIG.SPEED):
    return int(time * 1000/speed) # should be transfer into ms