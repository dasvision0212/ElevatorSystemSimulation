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

    isConnected = not False in visited.values()

    return predecessor, level, isConnected

def find_path(predecessor, target):
    v = target
    path = []
    while v is not None:
        path.append(v)
        v = predecessor[v]
    path.reverse()
    return path

floor_list = ["B4", "B3", "B2", "B1", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"]

available_list = [
    ['B4', 'B3', 'B2', 'B1', '1','2', '3', '4'],
    ["4", "5", "6", "7", "8", "9"],
    ["9","10", "11", "12", "13", "14", "15"]
]

# calculate adjacent matrix
adj_list = adjacent(floor_list,available_list)

# create spanning tree based on BFS
predecessor, level, isConnected = BFS(adj_list, start="1")

# find path from 1 to 15
p = find_path(predecessor, target="15")