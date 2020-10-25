from queue import Queue
import time
import itertools

floor_list = ["B4", "B3", "B2", "B1", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"]


group_setting = {
    'a': {
        'available_floor': [
            ['B4', 'B3', 'B1','1'], 
            ['1', '2', '3', '4', '5'],
            ['5', '6', '7', '8', '11', '12', '13', '14', '15'], 
            ['B3', 'B2'],
            ['8', '9', '10', '11']
        ],
    }
}
class Path_finder:
    def __init__(self, floorList, group_setting):
        available_list = []
        for sub_group_name in group_setting.keys():
                for available in group_setting[sub_group_name]['available_floor']:
                    available_list.append(available)
                    
        self.graph = self.adjacent(floorList, available_list)
        
        self.map = { floor: {floor: [] for floor in floorList} for floor in floorList}
        
        for i in floorList:
            for j in floorList:
                if i != j:
                    self.add_route(i,j)
        
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
        else:
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
            length = len(path)
            if length <= min_dist:
                
                # add precedents
                for i in range(length-1):
                    
                    # skip if path had been recorded
                    
                    value = (path[i+1], length-i-2)
                    if value in self.map[path[i]][path[-1]]:
                        break
                    self.map[path[i]][path[-1]].append( value )

t0 = time.time()
a = Path_finder(floor_list, group_setting)
t1 = time.time()
print(t1-t0)
a.map
