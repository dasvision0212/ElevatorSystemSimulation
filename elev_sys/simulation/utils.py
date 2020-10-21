# translate floor string to index (mostly becasue of 'B' prefix)
def floor_to_index(floor):
    return int(floor) if not 'B' in floor else -int(floor[1:]) + 1

# translate index to floor string
def index_to_floor(index):
    return str(index) if index > 0  else 'B'+str(-(index-1))

# return displacement of between two floor
def cal_displacement(f1, f2):
    f1 = int(f1) if not 'B' in f1 else -int(f1[1:]) + 1
    f2 = int(f2) if not 'B' in f2 else -int(f2[1:]) + 1
    return f2-f1

# return sign of displacement of between two floor
def compare_direction(f1, f2):
    d = cal_displacement(f1, f2)
    return 1 if d > 0 else (-1 if d < 0 else 0)

def advance_toward(f1, f2):
    return index_to_floor(floor_to_index(f1) + compare_direction(f1,f2))

def advance(floor, direction):
    return index_to_floor(floor_to_index(floor) + direction)


def floor_complement(floorList, available_floor):
    infeasible_floor = list()
    for floor in floorList:
        if(floor in available_floor):
            continue
        infeasible_floor.append(floor)

    return infeasible_floor