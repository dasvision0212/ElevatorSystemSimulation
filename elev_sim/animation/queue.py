from elev_sim.conf.log_conf import ELEVLOG_CONFIG
from elev_sim.conf.animation_conf import posConfig, colConfig
from elev_sim.animation.delay import (delay_by_interval, delay_by_time)


class Queue:
    debug = 1
    def __init__(self, now:list, canvas, posConfig, floorIndex, direction, log, name=None):
        self.riderNum   = 0

        self.now        = now
        self.canvas     = canvas
        self.posConfig  = posConfig
        self.floorIndex = floorIndex
        self.direction  = direction
        self.name       = name

        self.logPtr = 0
        self.log    = log

        self.coord1 = [
            self.posConfig.queue_left[self.direction], 
            self.posConfig.floorBase(self.floorIndex) - self.posConfig.queue_height
        ]

        self.coord2 = [
            self.posConfig.queue_right[self.direction], 
            self.posConfig.floorBase(self.floorIndex)
        ]

        self.queue = self.canvas.create_rectangle(*self.coord1, *self.coord2, fill=colConfig.queue[self.direction], width=0)
        self.customerLabel = self.canvas.create_text( \
            self.coord1[0] + (self.coord2[0] - self.coord1[0])/2, 
            self.coord1[1] + (self.coord2[1] - self.coord1[1])/2, 
            text=str(self.riderNum))

        if(self.log.shape[0] > 0):
            self.update()

    def update(self):
        if(self.logPtr > self.log.shape[0]-1):
            return

        currentAction = self.log.iloc[self.logPtr] 
        self.riderNum = int(currentAction["riderNumAfter"])
        self.canvas.itemconfigure(self.customerLabel, text=str(self.riderNum))
            
        if self.logPtr < self.log.shape[0]-1: # there exists another action to take # ignore the latest log
            nextAction = self.log.iloc[self.logPtr+1]
            self.logPtr += 1
            self.canvas.after(delay_by_time(nextAction["time"], self.now), self.update)        