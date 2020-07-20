class Block:
    def __init__(self, canvas_size, horizontal_grid, vertical_grid, grid_num=12):
        grid_unit = ((canvas_size[0])/grid_num, (canvas_size[1])/grid_num)

        self.left  = grid_unit[0] * horizontal_grid[0]
        self.right = grid_unit[0] * horizontal_grid[1]+1

        self.top   = grid_unit[1] * vertical_grid[0]
        self.btm   = grid_unit[1] * (vertical_grid[1]+1)

        self.center = ((self.left + self.right)/2, (self.top + self.btm)/2)

        print(vars(self))