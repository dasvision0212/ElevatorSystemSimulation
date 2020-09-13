import io
import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk


class WT_displayer:
    '''Waiting Time Displayer'''
    def __init__(self, env, canvas, posConfig, customer_log):
        self.env = env
        self.canvas = canvas
        self.posConfig = posConfig
        self.log = customer_log
        self.log.sort_values('boarding_time', inplace=True)

        self.logPtr = 0
        self.mean_WT = list()

        # if there is no statPic
        self.rectangle = self.canvas.create_rectangle(*self.posConfig.wt_block.coord, fill="white", width=0)
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
            if(currentRecord["boarding_time"] > self.env.now[0]):
                break
            
            if(len(self.mean_WT) == 0):
                self.mean_WT.append(currentRecord["waiting_time"])
            else:
                self.mean_WT.append(self.mean_WT[self.logPtr-1] * ((self.logPtr)/(self.logPtr+1)) + \
                                    currentRecord["waiting_time"]/(self.logPtr+1))            

                dpi = 80.0
                figsize = ((self.posConfig.wt_block.right-self.posConfig.wt_block.left)/dpi, 
                           (self.posConfig.wt_block.btm-self.posConfig.wt_block.top)/dpi)
                
                
                def get_img_from_fig(fig):
                    with io.BytesIO() as buf:
                        fig.savefig(buf, format="png")
                        buf.seek(0)
                        
                        img = buf.getvalue()

                        return img


                fig = plt.figure(num=None, figsize=figsize, dpi=dpi)
                plt.style.use('seaborn')
                plt.title('Average Waiting Time')
                plt.ylabel('average waiting time(seconds)')
                plt.xlabel('time')

                plt.plot(self.log["boarding_time"][:self.logPtr+1], self.mean_WT)

                width, height = fig.get_size_inches() * fig.get_dpi()
                width, height = int(width), int(height)
                
                self.img = tk.PhotoImage(width=width, height=height, data=get_img_from_fig(fig))
                
                if(self.rectangle != None):
                    self.statPic = self.canvas.create_image((self.posConfig.wt_block.left, self.posConfig.wt_block.top), 
                                                             anchor="nw", image=self.img)
                    self.canvas.delete(self.rectangle)
                    self.rectangle != None
                else:
                    self.canvas.itemconfigure(self.statPic, img=self.img)
                plt.close(fig)

            self.logPtr += 1
        self.canvas.after(self.env.delay_by_interval(1), self.update)