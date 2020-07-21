import threading
import tkinter as tk

from elev_sim.animation.animation import Animation


class Animation_ctrl:
    def __init__(self, building_name, elev_log_path, queue_log_path, elevatorList, floorList, title=None):
        self.terminate_event = threading.Event()
        self.check_terminate = threading.Event()
        self.animation = Animation(building_name, elev_log_path, queue_log_path, elevatorList, floorList, 
                                    self.terminate_event, self.check_terminate, title)
        self.status = True # True denotes processing, False denotes pausing

        self.thread = None

        self.window = tk.Tk()
        self.window.title("Elevator Animation Controller")

        # self.startButton = tk.Button(self.window, text="Start", command=self.start)
        # self.startButton.pack()

        self.pauseButton = tk.Button(self.window, text="Pause", command=self.pause)
        self.pauseButton.pack()

        # self.resumeButton = tk.Button(self.window, text="Resume", command=self.resume)
        # self.resumeButton.pack()

        self.closeButton = tk.Button(self.window, text="Close", command=self.terminate)
        self.closeButton.pack()

        self.exitCtrlButton = tk.Button(self.window, text="Close All", command=self.exitCtrl)
        self.exitCtrlButton.pack()

        self.window.mainloop()

    def start(self):
        if(not self.thread):
            self.thread = threading.Thread(name='Animation', target=self.animation.run)

    def pause(self):
        pass

    def terminate(self):
        if(not self.terminate_event.isSet()):
            self.terminate_event.set()
            self.check_terminate.wait()
            self.terminate_event.clear()
            self.check_terminate.clear()
            self.thread = None

    def exitCtrl(self):
        self.terminate()
        self.window.destroy()