import string
from itertools import combinations, permutations, product
def initElevatorGroups(elevators_list, floor_list, break_points):
#     print(elevators_list)
#     print(break_points)
    elevator_group = {}
    for index, elevators in enumerate(elevators_list):
        avalible_list = [[]]*(elevators)
        avalible_list[0] = floor_list
        infeasibles = []
        for i, break_point in enumerate(break_points[index]):
            position = avalible_list[i].index(break_point)
            avalible_list[i+1] =  avalible_list[i][position:]
            avalible_list[i] = avalible_list[i][:position+1]
            
        infeasibles = [ [floor for floor in floor_list if floor not in availble] for availble in avalible_list]
        
        # elevator group setting
        elevator_group[string.ascii_lowercase[index]] = {
            'infeasibles': infeasibles,
#             'availibles': avalible_list
        }
    return elevator_group
        
def elevator_group_permutation(elevators_num_list, floor_list):

    # permutation of number of elevators
    elevators_num_premutation = set() 
    for i in list(permutations(elevators_num_list)):
        if i not in elevators_num_premutation:
            elevators_num_premutation.add(i)
    elevators_num_premutation = list(elevators_num_premutation)
    
    # permutation of breaking points on floor layout
    break_points_list = [list(combinations(floor_list, n-1)) for n in elevators_num_list]
    break_points_perm = list(product(*break_points_list))

    # permutation of [breaking points] X [number of elevators]
    elevator_group_perm = []
    for break_points in break_points_perm:
        for elevators_num  in elevators_num_premutation:
            elevator_group = initElevatorGroups(elevators_num, floor_list, break_points)
            elevator_group_perm.append(elevator_group)
    
    return elevator_group_perm

# 對應的電梯數量
elevators_num_list = [3]

# 樓層
floor_list = ["B4", "B3", "B2", "B1", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"]

settings = elevator_group_permutation(elevators_num_list, floor_list)