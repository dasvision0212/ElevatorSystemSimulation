from elev_sim.conf.log_conf import ELEVLOG_CONFIG
from elev_sim.conf.animation_conf import colConfig, DEFAULT_ANIMA_CONFIG
from elev_sim.animation.env import Env
from elev_sim.animation.elevator import Elevator
from elev_sim.animation.queue import Queue


class Building:
    def __init__(self, env:Env, canvas, posConfig, name, elev_log, queue_log, elevatorList, floorList):
        self.env = env
        self.canvas = canvas
        self.posConfig = posConfig
        self.name = name
        self.elev_log = elev_log
        self.queue_log = queue_log

        # draw Elevator
        self.elevators = {name:Elevator(self.env, self.canvas, self.posConfig, name, i, 
                                        self.elev_log[self.elev_log["name"]==name], floorList) \
                                        for i, name in enumerate(elevatorList)}

        # draw queue
        self.queues = {
            1:[Queue(self.env, self.canvas, self.posConfig, floorIndex, 1, 
                self.queue_log[(self.queue_log["floorIndex"]==floorIndex) & (self.queue_log["direction"]==1)]) \
                for floorIndex in range(len(floorList))], 
                
            -1:[Queue(self.env, self.canvas, self.posConfig, floorIndex, -1,  
                self.queue_log[(self.queue_log["floorIndex"]==floorIndex) & (self.queue_log["direction"]==-1)]) \
                for floorIndex in range(len(floorList))]
        }

        # draw building
        # draw title
        self.canvas.create_rectangle(self.posConfig.building_left, self.posConfig.building_title_top, 
                                     self.posConfig.building_right, self.posConfig.building_title_btm, 
                                     fill=colConfig.building_title, width=0)

        self.canvas.create_text((self.posConfig.building_left+self.posConfig.building_right)/2,
                                (self.posConfig.building_title_top+self.posConfig.building_title_btm)/2, 
                                text=str(self.name), fill=colConfig.building_title_text)

        ## left wall
        self.canvas.create_rectangle(self.posConfig.building_left, self.posConfig.building_top, 
                                     self.posConfig.building_left + self.posConfig.building_wall, 
                                     self.posConfig.building_btm, 
                                     fill=colConfig.building, width=0)
        
        ## right wall
        self.canvas.create_rectangle(self.posConfig.building_right - self.posConfig.building_wall, 
                                     self.posConfig.building_top, 
                                     self.posConfig.building_right, self.posConfig.building_btm, 
                                     fill=colConfig.building, width=0)
        ## draw ceiling
        self.canvas.create_rectangle(self.posConfig.building_left, self.posConfig.building_top, 
                                     self.posConfig.building_right, 
                                     self.posConfig.building_top + self.posConfig.building_ceiling, 
                                     fill=colConfig.building, width=0)
        
        ## draw base
        self.canvas.create_rectangle(self.posConfig.building_left,
                                     self.posConfig.building_btm - self.posConfig.building_base,  
                                     self.posConfig.building_right + self.posConfig.source, 
                                     self.posConfig.building_btm, 
                                     fill=colConfig.building, width=0)
        
        ## draw horizontal gap
        floorNum = len(floorList)
        for i in range(floorNum-1):
            x1 = self.posConfig.building_left
            y1 = self.posConfig.building_top + self.posConfig.building_ceiling + \
                 self.posConfig.elev_height * (i+1) + self.posConfig.elev_gap_v * (i)
            
            x2 = self.posConfig.building_right + self.posConfig.source
            y2 = self.posConfig.building_top + self.posConfig.building_ceiling + \
                 self.posConfig.elev_height * (i+1) + self.posConfig.elev_gap_v * (i+1)
            
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=colConfig.building, width=0)
        
        ## draw horizontal gap
        for i in range(len(elevatorList)-1):
            x1 = self.posConfig.building_left + self.posConfig.building_wall + \
                 self.posConfig.elev_width * (i+1) + self.posConfig.elev_gap_h * (i)
            y1 = self.posConfig.building_top
            
            x2 = self.posConfig.building_left + self.posConfig.building_wall + \
                 self.posConfig.elev_width * (i+1) + self.posConfig.elev_gap_h * (i+1)
            y2 = self.posConfig.building_btm
            
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=colConfig.building, width=0)
        
        ## draw floor label
        for i, floorIndex in enumerate(floorList):
            x = self.posConfig.building_left - posConfig.floor_label_space
            y = self.posConfig.building_btm - self.posConfig.building_base - \
                i * (self.posConfig.elev_height + self.posConfig.elev_gap_v) - \
                self.posConfig.elev_height/2
            self.canvas.create_text(x, y, text=floorIndex, fill=colConfig.building_floor_label)

        ## draw queue label
        self.canvas.create_rectangle(self.posConfig.queue_left [1], self.posConfig.building_top, 
                                     self.posConfig.queue_right[1], self.posConfig.building_top + self.posConfig.building_ceiling, 
                                     fill=colConfig.queue_label[1], width=0)

        self.canvas.create_rectangle(self.posConfig.queue_left [-1], self.posConfig.building_top, 
                                     self.posConfig.queue_right[-1], self.posConfig.building_top + self.posConfig.building_ceiling, 
                                     fill=colConfig.queue_label[-1], width=0)

        self.canvas.create_text(*self.posConfig.queue_label [1], text="↑"  , fill=colConfig.queue_label_text[1])
        self.canvas.create_text(*self.posConfig.queue_label[-1], text="↓", fill=colConfig.queue_label_text[-1])