import matplotlib.pyplot as plt
import time
from itertools import count
from matplotlib.animation import FuncAnimation
import pandas as pd

simpleRun_ava = pd.read_csv('simpleRun_allava.csv')
wait_df = simpleRun_ava[simpleRun_ava['isSuccessful']==1]

x_vals = []
y_wait = []
y_jour = []

index = count()

wait_df['end_time'] = wait_df['appear_time'] + wait_df['journey_time']
wait_df = wait_df.sort_values(by=['end_time'])
y_wait_df = wait_df["total_waiting_time"]
y_jour_df = wait_df['journey_time']




def animate(i):

    cur_i = next(index)
    x_vals.append(cur_i)
    y_wait.append(y_wait_df[:cur_i].mean())
    y_jour.append(y_jour_df[:cur_i].mean())

    y_1 = y_wait
    y_2 = y_jour

    # clear grapg
    plt.cla()
    plt.plot(x_vals,y_wait,label='waiting_time')
    plt.plot(x_vals,y_jour,label='journey_time')
    
    plt.legend(loc='upper left')

    
    
ani = FuncAnimation(plt.gcf(),animate,interval=1000)

plt.legend(loc='upper left')
plt.tight_layout()
plt.show()