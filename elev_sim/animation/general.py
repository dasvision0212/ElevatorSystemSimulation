def displacement(floor1, floor2):
    floor1 = int(floor1) if not 'B' in floor1 else -int(floor1[1:]) + 1
    floor2 = int(floor2) if not 'B' in floor2 else -int(floor2[1:]) + 1
    return floor2-floor1


def cal_floorNum(FloorList):
    top = FloorList[-1]
    btm = FloorList[0]
    
    return abs(displacement(top, btm))+1