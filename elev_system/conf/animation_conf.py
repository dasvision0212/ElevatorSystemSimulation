from elev_system.conf.block import Block
from elev_system.conf.log_conf import STOPLIST_LOG_CONFIG

class DEFAULT_ANIMA_CONFIG:
    SPEED = 50

class colConfig:
    canvas_bg   = "#3b424b"
    building    = "#00a09d"
    
    queue_label = {
        1 :"#bebebe", 
        -1:"#bebebe"
    }

    queue_label_text = {
        1 :"black", 
        -1:"black"
    }

    queue = {
        1:"white", 
        -1:"white"
    }

    queue_text = {
        1:"black", 
        -1:"black"
    }

    building_title       = "#d8e4f0"
    building_title_text  = "black"
    building_floor_label = "white"

    elevator = "white"
    
    # Timer
    timer_text = "white"

    # stopList
    stopList_bg = "#dce1ee"
    stopList_border = canvas_bg
    stopList_dir_label = "white"
    stopList_floor_label = "white"

    sl_flag = {
        STOPLIST_LOG_CONFIG.NA     : "#9e9dc7", 
        STOPLIST_LOG_CONFIG.IDLE   : "#307d6e", 
        STOPLIST_LOG_CONFIG.ACTIVE : "#dc0e66"
    }

class posConfig: # position config
    window_size = (1200, 700)
    canvas_size = ((7./8)*window_size[0], (7./8)*window_size[1])
    
    elev_width       = 50
    elev_gap_h       = 20 # horizontal
    
    # block definition
    ## building
    floor_label_space = 10
    building_block    = Block((0, canvas_size[0]), (0, canvas_size[1]), 
                              horizontal_grid=(0, 6), vertical_grid=(0, 9))
   
    ## timer
    timer_block       = Block((0, canvas_size[0]), (0, canvas_size[1]), 
                              horizontal_grid=(10, 12), vertical_grid=(0, 1), padding=(10, 10))
    
    ## stopList
    sl_label_space = 10
    stopList_block    = Block((0, canvas_size[0]), (0, canvas_size[1]), 
                              horizontal_grid=(6, 12), vertical_grid=(1, 9), padding=(sl_label_space, 10, 10, 28))
    
    ## WT_displayer
    wt_block = Block((0, canvas_size[0]), (0, canvas_size[1]), 
                     horizontal_grid=(0, 6), vertical_grid=(9, 13), padding=(10, 10, 10, 10))

    ## JT_displayer
    jt_block = Block((0, canvas_size[0]), (0, canvas_size[1]), 
                     horizontal_grid=(6, 12), vertical_grid=(9, 13), padding=(10, 10, 10, 10))

    # building config
    building_title_top = building_block.top + 25
    building_title_btm = building_title_top + 25

    building_top     = building_title_btm
    building_btm     = building_block.btm - 25
    
    building_wall    = 20
    building_ceiling = 15
    building_base    = 15

    # queue config
    queue_padding = 0
    queue_width   = 25


    def __init__(self, elevatorNum, floorNum):
        self.source = posConfig.queue_padding * 3 + posConfig.queue_width * 2 # the place where customer wait for elevator
        
        # building config
        self.building_left  = posConfig.building_block.center[0] \
                            - posConfig.building_wall \
                            - posConfig.elev_gap_h * (elevatorNum-1)/2.0 \
                            - posConfig.elev_width * (elevatorNum)/2.0
        
        self.building_right = posConfig.building_block.center[0] + \
                              (posConfig.building_block.center[0] - self.building_left)
        
        self.elev_height = (posConfig.building_btm - posConfig.building_top - \
                            posConfig.building_ceiling - posConfig.building_base) * \
                            ((floorNum + 0.5)/(floorNum*2-1)) / (floorNum)
        
        self.elev_gap_v  = (posConfig.building_btm - posConfig.building_top - \
                            posConfig.building_ceiling - posConfig.building_base) * \
                            ((floorNum-1 - 0.5)/(floorNum*2-1)) / (floorNum-1) # vertical

        # source setting
        self.queue_height = self.elev_height
        self.queue_left = {
                1:self.building_right + posConfig.queue_padding # up
            }

        self.queue_right = {
                1:self.queue_left[1] + posConfig.queue_width # up
            }

        self.queue_left[-1] = self.queue_right[1] + posConfig.queue_padding # down
        self.queue_right[-1] = self.queue_left[-1] + posConfig.queue_width  # down

        self.queue_label = {
             1: [(self.queue_left[ 1] + self.queue_right[ 1])/2, self.building_top + 0.5*self.building_ceiling],
            -1: [(self.queue_left[-1] + self.queue_right[-1])/2, self.building_top + 0.5*self.building_ceiling]
        }

        # stopList config
        self.stopList_subBlock = [
            Block((posConfig.stopList_block.left, posConfig.stopList_block.right), 
                  (posConfig.stopList_block.top, posConfig.stopList_block.btm),
                  horizontal_grid=(0, elevatorNum), vertical_grid=(i, i+1), grid_num=elevatorNum, padding=(0, 0)) \
            for i in range(elevatorNum)
        ]

    def floorBase(self, floorIndex):
        return  self.building_btm - self.building_base - \
                floorIndex * (self.elev_gap_v + self.elev_height)