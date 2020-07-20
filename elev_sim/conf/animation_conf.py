from elev_sim.conf.block import Block


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

    elevator = "white"
    
class posConfig: # position config
    window_size = (1200, 700)
    canvas_size = ((7./8)*window_size[0], (7./8)*window_size[1])
    
    elev_width       = 50
    elev_gap_h       = 20 # horizontal
    
    # building config
    building_block = Block(canvas_size, horizontal_grid=(0, 11), vertical_grid=(0, 8))
    print(building_block.top, building_block.btm)

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

    def floorBase(self, floorIndex):
        return  self.building_btm - self.building_base - \
                floorIndex * (self.elev_gap_v + self.elev_height)

class DEFAULT_ANIMA_CONFIG:
    SPEED = 10
    SMOOTH = 3