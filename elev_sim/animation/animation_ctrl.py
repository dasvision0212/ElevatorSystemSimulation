import threading

from elev_sim.animation.animation import Animation


class Animation_ctrl:
    def __init__(self, building_name, elev_log_path, queue_log_path, elevatorList, floorList, title=None):
        Animation(building_name, elev_log_path, queue_log_path, elevatorList, floorList, title)


        