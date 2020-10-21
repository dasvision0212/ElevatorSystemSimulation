from queue import Queue
import itertools

def adjacent(floorList, available_list):
    adjacent_list = {}
    for floor in floorList:
        adjacent_list[floor] = []
    for available in available_list:
        for pair in itertools.permutations(available,2):
            if not pair[1] in adjacent_list[pair[0]]:
                adjacent_list[pair[0]].append(pair[1])
    return adjacent_list

def BFS(adjacent_list, start = '1'):
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
    s = start
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
    return predecessor, level

def find_path(predecessor, start):
    v = start
    path = []
    while v is not None:
        path.append(v)
        v = predecessor[v]
    path.reverse()
    return path