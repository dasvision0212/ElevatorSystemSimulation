import pandas as pd
import numpy as np


def move2floor_distribution(data_path):
    df = pd.read_json(data_path)
    df['time'] = df['result'].apply(lambda x:x['timestamp'])
    df['from'] = df['result'].apply(lambda x:x['from'])
    df['to'] = df['result'].apply(lambda x:x['to'])

    from_group = df.groupby('from')
    cols = np.sort(df['from'].unique())
    df_cols_baseCount = df.groupby('from')['to'].count()

    df = pd.DataFrame(columns=cols)

    for i,irow in from_group:
        to_group = irow.groupby('to')['result'].count()
        to_dict = {j:to_group[j]/df_cols_baseCount[i] if j in to_group.index else 0 for j in cols}
        to_dict[i] = 0
        df = df.append(to_dict,ignore_index=True)
    df = df.set_index(cols.tolist())
    df.to_csv(data_path[:-5]+'_move_distribution.csv')

# output move2floor distribution
data_path = '../data/Field3_Hotel.json'
move2floor_distribution(data_path)