from elev_sim.conf.log_conf import ELEVLOG_CONFIG
from elev_sim.conf.animation_conf import colConfig, DEFAULT_ANIMA_CONFIG
from elev_sim.animation.delay import (delay_by_interval, delay_by_time)


class Elevator:
    default_floor = 1
    def __init__(self, now:list, canvas, posConfig, name, index, log, floorList):
        self.posConfig = posConfig
        self.log = log
        self.now = now

        base_floor = int(floorList[0]) if not 'B' in floorList[0] else -int(floorList[0][1:]) + 1
        self.floorIndex = Elevator.default_floor-base_floor # 1st floort is not definitely on index 0, e.g. ["B1", "1"]
        self.name = name
        
        self.coord1 = [self.posConfig.building_left + self.posConfig.building_wall + \
                       index * (self.posConfig.elev_gap_h + self.posConfig.elev_width), 
                       self.posConfig.floorBase(self.floorIndex) - self.posConfig.elev_height]
        
        self.coord2 = [self.posConfig.building_left + self.posConfig.building_wall + \
                       index * (self.posConfig.elev_gap_h + self.posConfig.elev_width) + \
                       self.posConfig.elev_width, self.posConfig.floorBase(self.floorIndex)] 
                       
        self.riderNum = 0
        
        # the stuff about tkinter
        self.canvas = canvas
        
        self.elev = self.canvas.create_rectangle(*self.coord1, *self.coord2, fill=colConfig.elevator, width=0)
        self.riderLabel = self.canvas.create_text( \
            self.coord1[0] + (self.coord2[0] - self.coord1[0])/2, 
            self.coord1[1] + (self.coord2[1] - self.coord1[1])/2, 
            text=str(self.riderNum))
        
        self.logPtr = 0
        
        if(self.log.shape[0] > 0):
            self.update()
        
    def up(self):
        self.canvas.move(self.riderLabel, 0, -(self.posConfig.elev_gap_v + self.posConfig.elev_height)/DEFAULT_ANIMA_CONFIG.SMOOTH)
        self.canvas.move(self.elev, 0, -(self.posConfig.elev_gap_v + self.posConfig.elev_height)/DEFAULT_ANIMA_CONFIG.SMOOTH)
#         self.coord1[1] -= (self.posConfig.elev_gap_v + self.posConfig.elev_height)/SMOOTH
#         self.coord1[1] -= (self.posConfig.elev_gap_v + self.posConfig.elev_height)/SMOOTH
    
    def down(self):
        self.canvas.move(self.riderLabel, 0, (self.posConfig.elev_gap_v + self.posConfig.elev_height)/DEFAULT_ANIMA_CONFIG.SMOOTH)
        self.canvas.move(self.elev, 0, (self.posConfig.elev_gap_v + self.posConfig.elev_height)/DEFAULT_ANIMA_CONFIG.SMOOTH) 
#         self.coord1[1] += (self.posConfig.elev_gap_v + self.posConfig.elev_height)/SMOOTH
#         self.coord1[1] += (self.posConfig.elev_gap_v + self.posConfig.elev_height)/SMOOTH
    
    def update(self):
        if(self.logPtr > self.log.shape[0]-1):
            return

        currentAction = self.log.iloc[self.logPtr]
        if(currentAction["action"] == ELEVLOG_CONFIG.ARRIVE):
            self.current_floor = currentAction["riderNumAfter"]
        elif(currentAction["action"] == ELEVLOG_CONFIG.SERVE):
            self.riderNum = int(currentAction["riderNumAfter"])
            self.canvas.itemconfigure(self.riderLabel, text=str(self.riderNum))

        if self.logPtr < self.log.shape[0]-1: # there exists another action to take # ignore the latest log
            nextAction = self.log.iloc[self.logPtr+1]
            if(nextAction["action"] == ELEVLOG_CONFIG.ARRIVE):
                interval = (float)(nextAction["time"] - currentAction["time"])/3
                for i in range(3):
                    if(nextAction["direction"] == 1):
                        self.canvas.after(delay_by_interval(interval), self.up)
                    elif(nextAction["direction"] == -1):
                        self.canvas.after(delay_by_interval(interval), self.down)
                    else:
                        print(nextAction["direction"])
                        raise Exception("[!] invalid direction")
            self.logPtr += 1
            self.canvas.after(delay_by_time(nextAction["time"], self.now), self.update)