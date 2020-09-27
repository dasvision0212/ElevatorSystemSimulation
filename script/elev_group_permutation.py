import string
from itertools import combinations, permutations
def initElevatorGroups(sub_groups_num, elevators_list, floor_list, break_points):
    # 產出電梯結構
    elevator_group = {}
    
    # 分割樓層
    avalible_list = [[]]*sub_groups_num
    avalible_list[0] = floor_list
    for i, break_point in enumerate(break_points):
        index = avalible_list[i].index(break_point)
        avalible_list[i+1] =  avalible_list[i][index:]
        avalible_list[i] = avalible_list[i][:index+1]

    # 加入一樓
    for index, l in enumerate(avalible_list):
        for i in range(len(l)):
            if 'B' not in l[i]:
                avalible_list[index].insert(i, '1')
                break
            if 'B' in l[i]:
                if i + 1 == len(l):
                     avalible_list[index].append('1')
    
    # 建立小電梯組結構
    for i in range(sub_groups_num):
        infeasible = [floor for floor in floor_list if floor not in avalible_list[i]]
        elevator_group[string.ascii_lowercase[i]] = {
            'infeasible': infeasible,
            'elevNum': elevators_list[i]
        }
    return elevator_group


        
def elevator_group_permutation(sub_groups_num, elevators_num_list, floor_list):

    # 所有小電梯中電梯數量的組合
    elevators_num_premutation = set() 
    for i in list(permutations(elevators_num_list)):
        if i not in elevators_num_premutation:
            elevators_num_premutation.add(i)
    elevators_num_premutation = list(elevators_num_premutation)
    
    # 所有樓層切割點
    floor_list.remove("1")
    break_points_list = list(combinations(floor_list, sub_groups_num-1))
    
    # 所有電梯組組合
    elevator_group_perm = []
    for break_points in break_points_list:
        for elevators_num  in elevators_num_premutation:
            elevator_group = initElevatorGroups(sub_groups_num, elevators_num, floor_list, break_points)
            elevator_group_perm.append(elevator_group)
    
    return elevator_group_perm

# 小電梯組數
sub_groups_num = 2

# 對應的電梯數量
elevators_num_list = [2,2]

# 樓層
floor_list = ["B4", "B3", "B2", "B1", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"]

print(elevator_group_permutation(sub_groups_num, elevators_num_list, floor_list))