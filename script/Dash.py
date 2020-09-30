#-*- coding: UTF-8 -*-

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

data = pd.read_csv('../data/simulation_multipleTimes.csv')

locationList = data.location.unique()
elevSup_NumPairList = data.elevator_subgroup_number.unique()
middle_floorList = data.policy_middle_floor.unique()



###########  end import data  #############

21,22,23,31,32,41

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
        html.Label('Middle Floor'),
    	dcc.Dropdown(
                id='middle_floor',
                options=[{'label':i, 'value':i} for i in middle_floorList],
                value='7'
    	),
        html.Label('elevator subgroup number'),
    	dcc.Dropdown(
                id='elevSup_NumPair',
                options=[{'label':i, 'value':i} for i in elevSup_NumPairList],
                value='[2, 1]'
    	)
    ],style={'width': '15%', 'display': 'inline-block'}),
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
    Input('middle_floor','value'),
    Input('elevSup_NumPair','value')
    ]
)



def update_graph(location, middle_floor,elevSup_NumPair):
    df = data[(data["location"] == location) & (data["policy_middle_floor"] == middle_floor) & (data["elevator_subgroup_number"] == elevSup_NumPair) ]
    if len(df) == 0:
        pass
    else:
        fig = px.histogram(df, x= "Time", title=location, facet_col="TimeType", color="TimeType")
    fig.update_layout(title_text=location)

    return fig



if __name__ == '__main__':
    app.run_server(debug=True)





