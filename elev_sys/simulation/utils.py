from collections import namedtuple

import pandas as pd
import scipy.stats as st

class IAT_Distribution:
    '''
    inter-arrival time distribution
    '''

    def __init__(self, path):
        self.df = pd.read_csv(path)
        # self.df["floor"] = self.df["floor"].apply(lambda x: x.lstrip('0'))

    def getter(self, direction, floor):

        # # filter row by mulitple conditions
        # if floor in self.df['floor']:
        #     return None
        
        temp = self.df[(self.df['direction'] == direction) & (self.df['floor'].astype(str) == floor)][['dist', 'parameters']]
        
        if(temp.shape[0] == 0):
            return None
        else:
            # return distribution name and parsed parameters
            return {
                'dist': getattr(st, temp['dist'].values[0]),
                'params': self.params_parser(temp['parameters'].values[0])
            }

    @staticmethod
    def params_parser(params_string):
        params = []
        for param in params_string.replace("(", "").replace(")", "").split(", "):
            params.append(float(param))
        return params

Mission = namedtuple("Mission", ["direction", "destination"])

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