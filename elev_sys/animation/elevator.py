from elev_sys.conf.log_conf import ELEVLOG_CONFIG
from elev_sys.conf.animation_conf import colConfig, DEFAULT_ANIMA_CONFIG
from elev_sys.animation.env import Env

class Elevator:
    default_floor = 1
    def __init__(self, env:Env, canvas, posConfig, name, index, log, floorList):
        self.posConfig = posConfig
        self.log = log
        self.env = env

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
        self.canvas.move(self.riderLabel, 0, -(self.posConfig.elev_gap_v + self.posConfig.elev_height))
        self.canvas.move(self.elev, 0, -(self.posConfig.elev_gap_v + self.posConfig.elev_height))
#         self.coord1[1] -= (self.posConfig.elev_gap_v + self.posConfig.elev_height)/SMOOTH
#         self.coord1[1] -= (self.posConfig.elev_gap_v + self.posConfig.elev_height)/SMOOTH
    
    def down(self):
        self.canvas.move(self.riderLabel, 0, (self.posConfig.elev_gap_v + self.posConfig.elev_height))
        self.canvas.move(self.elev, 0, (self.posConfig.elev_gap_v + self.posConfig.elev_height)) 
#         self.coord1[1] += (self.posConfig.elev_gap_v + self.posConfig.elev_height)/SMOOTH
#         self.coord1[1] += (self.posConfig.elev_gap_v + self.posConfig.elev_height)/SMOOTH
    
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

            if(currentAction["action"] == ELEVLOG_CONFIG.ARRIVE):
                self.current_floor = currentAction["floor"]
                if(currentAction["direction"] == 1):
                    self.up()
                elif(currentAction["direction"] == -1):
                    self.down()
                else:
                    print(currentAction["direction"])
                    raise Exception("[!] invalid direction")

            elif(currentAction["action"] == ELEVLOG_CONFIG.SERVE):
                self.riderNum = int(currentAction["riderNumAfter"])
                self.canvas.itemconfigure(self.riderLabel, text=str(self.riderNum))

            self.logPtr += 1
        self.canvas.after(self.env.delay_by_interval(1), self.update)