from elev_sim.conf.log_conf import ELEVLOG_CONFIG
from elev_sim.conf.animation_conf import posConfig, colConfig
from elev_sim.animation.env import Env


class Queue:
    debug = 1
    def __init__(self, env:Env, canvas, posConfig, floorIndex, direction, log, name=None):
        self.riderNum   = 0

        self.env        = env
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
        if(not self.env.status):
            self.canvas.after(self.env.delay_by_interval(1), self.update)
            return

        if(self.logPtr > self.log.shape[0]-1):
            return

        while(self.logPtr <= self.log.shape[0]-1):
            currentAction = self.log.iloc[self.logPtr]
            if(currentAction["time"] > self.env.now[0]):
                break
            
            self.riderNum = int(currentAction["riderNumAfter"])
            self.canvas.itemconfigure(self.customerLabel, text=str(self.riderNum))        

            self.logPtr += 1

        self.canvas.after(self.env.delay_by_interval(1), self.update) 