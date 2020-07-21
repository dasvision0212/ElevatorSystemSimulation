import time
import tkinter as tk
import pandas as pd
import threading
from collections import defaultdict

from elev_sim.conf.NTUH_conf  import ELEV_INFEASIBLE
from elev_sim.conf.log_conf  import ELEVLOG_CONFIG
from elev_sim.animation.building  import Building
from elev_sim.conf.animation_conf import (colConfig, posConfig)
from elev_sim.animation.env import Env
from elev_sim.animation.general import cal_floorNum
from elev_sim.animation.timer import Timer
from elev_sim.animation.stopList import StopList

class Animation:
    def __init__(self, building_name, elev_log_path, queue_log_path, stopList_log_path, 
                 elevatorList, floorList, elev_infeasible:defaultdict=ELEV_INFEASIBLE, title=None):
        self.env = Env()

        self.elev_log = pd.read_csv(elev_log_path)
        self.elev_log["name"] = self.elev_log["name"].astype(str)

        self.queue_log = pd.read_csv(queue_log_path)
        self.queue_log["floorIndex"] = self.queue_log["floorIndex"].astype(int)

        self.stopList_log = pd.read_csv(stopList_log_path)
        self.stopList_log["elevIndex"] = self.stopList_log["elevIndex"].astype(str)

        # the stuff about tkinter
        self.posConfig = posConfig(len(elevatorList), cal_floorNum(floorList))
        self.building_name = building_name

        self.window = tk.Tk()
        if(title != None):
            self.window.title(title)
        else:
            self.window.title("Elevator Animation")

        self.window_size = self.posConfig.window_size
        
#         self.window_size[0], self.window_size[1] = self.window.maxsize()
#         self.window_size[1] -= 50
        
        self.window.geometry("{}x{}".format(self.window_size[0], self.window_size[1])) # ! the format is of string, not of int
        self.window.resizable(0,0) #不可以更改大⼩
        
        self.canvas = tk.Canvas(self.window, width=self.posConfig.canvas_size[0], height=self.posConfig.canvas_size[1], 
                                bg = colConfig.canvas_bg)
        hbar = tk.Scrollbar(self.window, orient = "horizontal")
        hbar.pack(side="bottom",fill='x')
        hbar.config(command=self.canvas.xview)
        
        vbar = tk.Scrollbar(self.window,orient="vertical")
        vbar.pack(side="right",fill='y')
        vbar.config(command=self.canvas.yview)
        
        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.pack(side="left",expand=True,fill="both")
        
        # widget
        self.building = Building(self.env, self.canvas, self.posConfig, self.building_name, 
                                 self.elev_log, self.queue_log,elevatorList, floorList)
        
        self.timer = Timer(self.env, self.canvas, self.posConfig)
        
        # self, env, canvas, posConfig, name, index, log, floorList
        self.stopList = {
            StopList(self.env, self.canvas, self.posConfig, elevIndex, i, 
            self.stopList_log[self.stopList_log["elevIndex"]==elevIndex], floorList, elev_infeasible) \
            for i, elevIndex in enumerate(elevatorList)
        }

        # time fleet
        self.window.after(0, self.time_fleet)

        # button
        self.closeButton = tk.Button(self.window, text="Shut Down", command=self.window.destroy)
        self.closeButton.pack()

        self.pauseButton = tk.Button(self.window, text="Continue", command=self.progress)
        self.pauseButton.pack()

        self.window.mainloop()
        
    def time_fleet(self):
        if(self.env.status):
            self.env.now[0] += 1
        self.window.after(self.env.delay_by_interval(1), self.time_fleet)

    def progress(self):
        '''deal with pause'''
        self.env.status = not self.env.status



