import pandas as pd
import scipy.stats as st

class IAT_Distribution:
    '''
    inter-arrival time distribution
    '''

    def __init__(self, path):
        self.df = pd.read_csv(path)
        print(path)
        print(self.df.head())
        self.df["Floor"] = self.df["Floor"].apply(lambda x: x.lstrip('0'))

    def getter(self, location, section, direction, floor):

        # filter row by mulitple conditions
        temp = self.df[(self.df['Location'] == location) & (self.df['Section'] == section) &
                       (self.df['Direction'] == direction) & (self.df['Floor'] == floor)][['Distribution', 'Parameters']]

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