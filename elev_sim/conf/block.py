class Block:
    def __init__(self, x, y, horizontal_grid, vertical_grid, grid_num=12, padding=(0, 0)):
        if(len(padding) == 2):
            padding = (padding[0], padding[1], padding[0], padding[1])

        grid_unit = ((x[1] - x[0])/grid_num, (y[1] - y[0])/grid_num)

        self.left  = x[0] + grid_unit[0] * horizontal_grid[0] + padding[0]
        self.right = x[0] + grid_unit[0] * (horizontal_grid[1]) - padding[2]

        self.top   = y[0] + grid_unit[1] * vertical_grid[0] + padding[1]
        self.btm   = y[0] + grid_unit[1] * (vertical_grid[1]) - padding[3]

        self.center = (x[0] + (self.left + self.right)/2, y[0] + (self.top + self.btm)/2)