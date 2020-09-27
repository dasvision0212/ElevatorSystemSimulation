import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import math
import plotly.express as px
import pandas as pd
from random import randint
import numpy as np

import sys

###########  import data  #############

data = pd.read_csv('v2v3.csv',names=['location','floorNum', 'version', 'eleNum','TimeType','Time'])

locationList = data.location.unique()
eleNumList = data.eleNum.unique()
floorNumList = data.floorNum.unique()
versionList = data.version.unique()
versionList.sort()


###########  end import data  #############



app = dash.Dash()

app.layout = html.Div([
    html.H2(children='Waiting time & Journey time'),
    html.Div([
        html.Label('Building'),
    	dcc.Dropdown(
	        id="location",
	        options=[{'label': i, 'value': i} for i in locationList],
	        value='研究大樓'
    	),
        html.Label('Elevator Number'),
    	dcc.Dropdown(
                id='eleNum',
                options=[{'label': i, 'value': i} for i in eleNumList],
                value=5
    	),
        html.Label('Floor Number'),
    	dcc.Dropdown(
                id='floorNum',
                options=[{'label': i, 'value': i} for i in floorNumList],
                value=19
    	)
    ],style={'width': '20%', 'display': 'inline-block'}),
    html.Div([
        html.Label('Version'),
        dcc.RadioItems(
                id='version',
                options=[{'label': i, 'value': i} for i in versionList],
                value=3,
                labelStyle={'display': 'inline-block'}
        )
    ],style={'width': '20%', 'display': 'block'}),
    dcc.Graph(
        id="GraphMeasurement"
    )
])

# interact
# location = "NHB"
# eleNum = 5
# floorNum = 15
# version = 3
###

@app.callback(
    Output('GraphMeasurement','figure'),
    [Input('location','value'),
    Input('eleNum','value'),
    Input('floorNum','value'),
    Input('version','value')
    ]
)



def update_graph(location, eleNum,floorNum, version):
	df = data[(data["location"] == location) & (data["eleNum"] == eleNum) & (data["floorNum"]==floorNum) & (data["version"] == version ) ]
	fig = px.histogram(df
							, x= 'Time'
							, title=location
							, facet_col="TimeType",color="TimeType"
							)
	fig.update_layout(title_text=location)
	return fig



if __name__ == '__main__':
    app.run_server(debug=True)




###########  simulate data  #############
# locationList = ['NHB', 'SHB', 'SC', 'Research']
# eleNumList = range(1,6)
# floorNumList = [5, 15]
# versionList = [2, 3, 4]

# data = []
# for location in locationList:
#   for eleNum in eleNumList:
#       for floorNum in floorNumList:
#           for version in versionList:
#               for simulation in range(10):
#                   waitT = randint(100,200)
#                   JourneyT =  waitT+ randint(100,150)
#                   data.append({
#                         'location': location, 
#                         'eleNum': eleNum,
#                         'floorNum': floorNum,
#                         'version': version,
#                         'TimeType': 'Waiting time',
#                         'Time': waitT})
#                   data.append({
#                         'location': location, 
#                         'eleNum': eleNum,
#                         'floorNum': floorNum,
#                         'version': version,
#                         'TimeType': 'Journey time',
#                         'Time': JourneyT})
                
#               # data.to_csv('tryData.csv', mode = 'a', header = False, index= False)

# data = pd.DataFrame(data)

###########  end simulate data  #############

########### try ############


########### end try ############
