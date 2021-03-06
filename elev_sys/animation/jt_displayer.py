import io
import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from copy import deepcopy
import json


class JT_displayer:
    '''Journey Time Displayer'''
    def __init__(self, env, canvas, posConfig, customer_log):
        self.env = env
        self.canvas = canvas
        self.posConfig = posConfig
        self.log = deepcopy(customer_log)
        self.log = self.log.loc[self.log.isSuccessful, :]
        self.log["leave_time"] = self.log["get_off_time"].apply(lambda x:x[-1])
        self.log.sort_values('leave_time', inplace=True)

        self.logPtr = 0
        self.mean_JT = list()

        # if there is no statPic
        self.rectangle = self.canvas.create_rectangle(*self.posConfig.jt_block.coord, fill="white", width=0)
        self.img     = None   # it exists to prevent that python garbage collectort discard the img reference that tkinter needs
                              # http://effbot.org/pyfaq/why-do-my-tkinter-images-not-appear.htm
        self.statPic = None

        self.update()

    def update(self):
        if(not self.env.status):
            self.canvas.after(self.env.delay_by_interval(1), self.update)
            return
        
        if(self.logPtr > self.log.shape[0]-1):
            return
        
        while(self.logPtr <= self.log.shape[0]-1):
            currentRecord = self.log.iloc[self.logPtr,]
            if(currentRecord["leave_time"].seconds > self.env.now[0]):
                break
            
            if(len(self.mean_JT) == 0):
                self.mean_JT.append(currentRecord["journey_time"])
            else:
                self.mean_JT.append(self.mean_JT[self.logPtr-1] * ((self.logPtr)/(self.logPtr+1)) + \
                                    currentRecord["journey_time"]/(self.logPtr+1))            

                dpi = 80.0
                figsize = ((self.posConfig.jt_block.right-self.posConfig.jt_block.left)/dpi, 
                           (self.posConfig.jt_block.btm-self.posConfig.jt_block.top)/dpi)
                
                
                def get_img_from_fig(fig):
                    with io.BytesIO() as buf:
                        fig.savefig(buf, format="png")
                        buf.seek(0)
                        
                        img = buf.getvalue()

                        return img


                fig = plt.figure(num=None, figsize=figsize, dpi=dpi)
                plt.style.use('seaborn')

                plt.title('Average Journey Time')
                plt.ylabel('average journey time(seconds)')
                plt.xlabel('time')

                plt.plot(self.log["leave_time"][:self.logPtr+1], self.mean_JT)
                
                width, height = fig.get_size_inches() * fig.get_dpi()
                width, height = int(width), int(height)
                
                self.img = tk.PhotoImage(width=width, height=height, data=get_img_from_fig(fig))
                
                if(not self.rectangle is None):
                    self.statPic = self.canvas.create_image((self.posConfig.jt_block.left, self.posConfig.jt_block.top), 
                                                             anchor="nw", image=self.img)
                    self.canvas.delete(self.rectangle)
                    self.rectangle = None
                else:
                    self.canvas.itemconfigure(self.statPic, image=self.img)


            self.logPtr += 1
        self.canvas.after(self.env.delay_by_interval(1), self.update)