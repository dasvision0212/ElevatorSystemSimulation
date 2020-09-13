from elev_system.conf.animation_conf import colConfig
from elev_system.conf.log_conf import STOPLIST_LOG_CONFIG


class StopList:
    def __init__(self, env, canvas, posConfig, name, index, log, floorList, elev_infeasible):
        self.env = env
        self.canvas = canvas
        self.name = name
        self.index = index
        self.log = log.reset_index()
        self.floorList = floorList
        self.infeasible = elev_infeasible[self.name]

        self.posConfig = posConfig
        self.block = self.posConfig.stopList_subBlock[self.index]

        self.logPtr = 0
        
        self.bg = self.canvas.create_rectangle(self.block.left, self.block.top, self.block.right, self.block.btm, 
                                     fill=colConfig.stopList_bg, 
                                     outline=colConfig.stopList_border, width=5)


        # stopList posConfig
        floorNum = len(self.floorList)
        width_wight = floorNum / 2
        self.floor_width = ((self.block.right - self.block.left) * \
                           ((floorNum + width_wight)/(floorNum*2+1)) / (floorNum))
        
        self.floor_gap_h = ((self.block.right - self.block.left) * \
                           ((floorNum+1 - width_wight)/(floorNum*2+1)) / (floorNum+1)) # vertical

        listNum = 2
        self.floor_height = ((self.block.btm - self.block.top) * \
                           ((listNum + 0.5)/(listNum*2+1)) / (listNum))
        
        self.floor_gap_v = ((self.block.btm - self.block.top) * \
                           ((listNum+1 - 0.5)/(listNum*2+1)) / (listNum+1)) # vertical


        # draw list
        self.stop_list = dict()
        self.stop_list[1] = list()
        for i, floor in enumerate(floorList):
            color = None
            if(floor in self.infeasible):
                color = colConfig.sl_flag[STOPLIST_LOG_CONFIG.NA]
            else:
                color = colConfig.sl_flag[STOPLIST_LOG_CONFIG.IDLE]
            self.stop_list[1].append(self.canvas.create_rectangle(*self.floorCoord(1, i), 
                                         fill=color, 
                                         width=0))

        self.stop_list[-1] = list()
        for i, floor in enumerate(floorList):
            color = None
            if(floor in self.infeasible):
                color = colConfig.sl_flag[STOPLIST_LOG_CONFIG.NA]
            else:
                color = colConfig.sl_flag[STOPLIST_LOG_CONFIG.IDLE]
            self.stop_list[-1].append(self.canvas.create_rectangle(*self.floorCoord(-1, i), 
                                         fill=color, 
                                         width=0))

        # add label
        font = ("Calibri", 8)
        self.floor_label = dict()
        compareBase = self.floorCoord(1, 0)
        self.floor_label[1] = self.canvas.create_text(
                                posConfig.stopList_block.left - posConfig.sl_label_space/2, 
                                (compareBase[1] + compareBase[3])/2, 
                                text="↑", 
                                fill=colConfig.stopList_dir_label
                                )

        compareBase = self.floorCoord(-1, 0)
        self.floor_label[-1] = self.canvas.create_text(
                                posConfig.stopList_block.left - posConfig.sl_label_space/2, 
                                (compareBase[1] + compareBase[3])/2, 
                                text="↓", 
                                fill=colConfig.stopList_dir_label
                                )

        
        self.floor_label = dict()
        self.floor_label[1] = [
            self.canvas.create_text(*self.floorTextCoord(1, i), text=floor, fill=colConfig.stopList_floor_label, font=font) \
            for i, floor in enumerate(self.floorList)
        ]

        self.floor_label[-1] = [
            self.canvas.create_text(*self.floorTextCoord(-1, i), text=floor, fill=colConfig.stopList_floor_label, font=font) \
            for i, floor in enumerate(self.floorList)
        ]

        if(self.log.shape[0] > 0):
            self.update()

    def floorCoord(self, direction, floorIndex):
        if(direction == 1):
            left = self.block.left + self.floor_gap_h + floorIndex * (self.floor_width + self.floor_gap_h)
            top = self.block.top + self.floor_gap_v
            right = self.block.left + self.floor_gap_h + floorIndex * (self.floor_width + self.floor_gap_h) + self.floor_width
            btm = self.block.top + self.floor_gap_v + self.floor_height

            return(left, top, right, btm)

        else:
            floorIndex_r = len(self.floorList)-1-floorIndex
            left = self.block.left + self.floor_gap_h + floorIndex_r * (self.floor_width + self.floor_gap_h)
            top = self.block.btm - self.floor_gap_v - self.floor_height
            right = self.block.left + self.floor_gap_h + floorIndex_r * (self.floor_width + self.floor_gap_h) + self.floor_width
            btm = self.block.btm - self.floor_gap_v
            
            return(left, top, right, btm)


    def floorTextCoord(self, direction, floorIndex):
        coord = self.floorCoord(direction, floorIndex)
        return((coord[0] + coord[2]) / 2, (coord[1] + coord[3]) / 2)


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

            floorIndex = None
            if(currentAction["direction"] == 1):
                floorIndex = int(currentAction["floorIndex"])
            elif(currentAction["direction"] == -1):
                floorIndex = len(self.floorList) - 1 - int(currentAction["floorIndex"])
            else:
                raise Exception("[!] Invalid direction when reading the stopList_log. ")

            self.canvas.itemconfigure(self.stop_list[int(currentAction["direction"])][floorIndex], 
                                      fill=colConfig.sl_flag[int(currentAction["latterStatus"])])
            
            self.logPtr += 1
        self.canvas.after(self.env.delay_by_interval(1), self.update)
    