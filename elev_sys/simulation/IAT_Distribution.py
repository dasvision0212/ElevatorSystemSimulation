import pandas as pd
import scipy.stats as st

class IAT_Distribution:
    '''
    inter-arrival time distribution
    '''

    def __init__(self, path, location, section):
        self.df = pd.read_csv(path)
        self.df["Floor"] = self.df["Floor"].apply(lambda x: x.lstrip('0'))
        self.location = location
        self.section = section

    def getter(self, direction, floor):
        direction_string = None
        if direction == 1:
            direction_string = 'up'
        elif direction == -1:
            direction_string = 'down'

        # filter row by mulitple conditions
        if floor in self.df['Floor']:
            return None
        
        temp = self.df[(self.df['Location'] == self.location) & (self.df['Section'] == self.section) &
                    (self.df['Direction'] == direction_string) & (self.df['Floor'] == floor)][['Distribution', 'Parameters']]
        
        if(temp.shape[0] == 0):
            return None
        else:
            # return distribution name and parsed parameters
            return {
                'dist': getattr(st, temp['Distribution'].values[0]),
                'params': self.params_parser(temp['Parameters'].values[0])
            }

    @staticmethod
    def params_parser(params_string):
        params = []
        for param in params_string.replace("(", "").replace(")", "").split(", "):
            params.append(float(param))
        return params