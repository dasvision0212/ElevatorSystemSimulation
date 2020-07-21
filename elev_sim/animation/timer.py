from elev_sim.animation.env import Env
from elev_sim.conf.animation_conf import colConfig
import datetime

class Timer:
    def __init__(self, env:Env, canvas, posConfig):
        self.env = env
        self.canvas = canvas
        self.posConfig = posConfig

        self.timeText = self.canvas.create_text( \
            self.posConfig.timer_block.center[0], 
            self.posConfig.timer_block.center[1], 
            text=str(datetime.timedelta(seconds=self.env.now[0])), 
            fill=colConfig.timer_text, 
            font=("Calibri", 20))

        self.update()

    def update(self):
        if(not self.env.status):
            self.canvas.after(self.env.delay_by_interval(1), self.update)
            return
            
        self.canvas.itemconfigure(self.timeText, text=str(datetime.timedelta(seconds=self.env.now[0]))) 
        self.canvas.after(self.env.delay_by_interval(1), self.update)