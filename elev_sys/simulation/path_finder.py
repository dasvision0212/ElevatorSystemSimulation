from queue import Queue
import time
import itertools

class Path_finder:
    def __init__(self, floorList, group_setting, fileName=None):
        
        # extract available floor list
        self.elevNum = 0
        available_list = []
        for sub_group_name in group_setting.keys():
            self.elevNum = self.elevNum + len(group_setting[sub_group_name]['available_floor'])
            for available in group_setting[sub_group_name]['available_floor']:
                available_list.append([floor for floor in available if floor in floorList])
                    
        self.graph = self.adjacent(floorList, available_list)
        
        self.map = None
        if(fileName is None):
            # compute all pair's all shortest paths
            self.map = { floor: {floor: [] for floor in floorList} for floor in floorList}
            for pair in itertools.combinations(floorList,2):
                self.add_route(*pair)
        else:
            with open(fileName, 'r') as file:
                import json
                self.map = json.load(file)
        
    def adjacent(self, floor_list, available_list):
        adjacent_list = {}
        for floor in floor_list:
            adjacent_list[floor] = []
        for available in available_list:
            for pair in itertools.permutations(available,2):
                if not pair[1] in adjacent_list[pair[0]]:
                    adjacent_list[pair[0]].append(pair[1])
        return adjacent_list
    
    def find_all_path_recursive(self, s, d, visited, path, path_list): 
        visited[s]= True
        path.append(s) 
        
        if s == d:
            path_list.append(path.copy())
        elif len(path) < self.elevNum + 1:
            for i in self.graph[s]: 
                if visited[i]== False: 
                    self.find_all_path_recursive(i, d, visited, path, path_list)
        
        path.pop() 
        visited[s]= False
        
    def find_all_path(self, s, d):
        visited = {}
        for node in self.graph.keys():
            visited[node] = False
        
        path = []
        path_list = []
        self.find_all_path_recursive(s, d, visited, path, path_list)
        return path_list
        
    def add_route(self, i, j):
        
        # all paths
        path_list = self.find_all_path(i, j)
        
        # length of shortest path
        min_dist = min( map(len, path_list) )
    
        for path in path_list:
            
            # length threshold
            if len(path) <= min_dist:
               
                # append path in bidirection
                self.map[i][j].append( path.copy() )
                path.reverse()
                self.map[j][i].append( path.copy() )