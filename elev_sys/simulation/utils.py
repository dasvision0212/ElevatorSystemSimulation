def floor_to_index(floor):
# translate floor string to index (mostly becasue of 'B' prefix)
    return int(floor) if not 'B' in floor else -int(floor[1:]) + 1


def index_to_floor(index):
# translate index to floor string
    return str(index) if index > 0  else 'B'+str(-(index-1))


def cal_displacement(f1, f2):
# return displacement of between two floor
    f1 = int(f1) if not 'B' in f1 else -int(f1[1:]) + 1
    f2 = int(f2) if not 'B' in f2 else -int(f2[1:]) + 1
    return f2-f1


def compare_direction(f1, f2):
# return sign of displacement of between two floor
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