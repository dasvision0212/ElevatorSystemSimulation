from itertools import permutations
from queue import Queue
import itertools


def adjacent(floorList, available_floor):
    adjacent_list = {}
    for floor in floorList:
        adjacent_list[floor] = []
    for available in available_floor:
        for pair in itertools.permutations(available,2):
            if not pair[1] in adjacent_list[pair[0]]:
                adjacent_list[pair[0]].append(pair[1])
    return adjacent_list


def next_transfer(adjacent_list, source):
    visited = {}
    queue = Queue()
    predecessor = {}
    level = {}

    # inititialization
    for node in adjacent_list.keys():
        visited[node] = False
        predecessor[node] = None
        level[node] = -1

    # start node
    s = source
    visited[s] = True
    level[s] = 0
    queue.put(s)
    
    # traversal
    while not queue.empty():
        u = queue.get()
        for v in adjacent_list[u]:
            if not visited[v]:
                visited[v] = True
                predecessor[v] = u
                level[v] = level[u] + 1
                queue.put(v)

    isConnected = not False in visited.values()

    return predecessor, level, isConnected


def find_path(predecessor, destination):
    pass_by = destination
    path = []
    while pass_by is not None:
        path.append(pass_by)
        pass_by = predecessor[pass_by]
    path.reverse()
    return path


class Path_finder:
    def __init__(self, floorList, group_setting):
        self.predecessor_dict = dict()
        for elevNum in range(len(group_setting.keys()), 0, -1):
            for elev_combination in itertools.combinations(group_setting.keys(), elevNum):
                available_floor = list()
                for elevName in elev_combination:
                    for available in group_setting[elevName]["available_floor"]:
                        available_floor.append(available)

                    key = frozenset(elev_combination)
                    self.predecessor_dict[key] = dict()

                    adjacent_list = adjacent(floorList, available_floor)
                    for floor in floorList:
                        self.predecessor_dict[key][floor] = next_transfer(adjacent_list, floor)[0]

        # with open("../../data/path_log.json", 'w', encoding="utf-8") as file:
        #     import json
        #     json.dump(predecessor_dict, file, ensure_ascii=False)



