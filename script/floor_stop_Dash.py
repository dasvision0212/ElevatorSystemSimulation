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

data = pd.read_csv('../data/floor_count.csv')

locationList = data.location.unique()
elevSup_NumPairList = data.elevator_subgroup_number.unique()
floor_policyList = data.floor_policy.unique()



###########  end import data  #############


app = dash.Dash()

app.layout = html.Div([
    html.H2(children='stop count & floor count'),
    html.Div([
        html.Label('電梯組'),
        dcc.Dropdown(
            id="location",
            options=[{'label': i, 'value': i} for i in locationList],
            value='研究大樓'
        ),
        html.Label('電梯分層政策'),
        dcc.Dropdown(
                id='floor_policy',
                options=[{'label':i, 'value':i} for i in floor_policyList],
                value="all_feasible"
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
    Input('floor_policy','value')
    ]
)



def update_graph(location, floor_policy):
    df = data[(data["location"] == location) & (data["floor_policy"] == floor_policy)]
    if len(df) == 0:
        pass
    else:
        fig = px.histogram(df, x= "floor_count", title=location, facet_col="count_type", color="count_type")
    fig.update_layout(title_text=location)

    return fig



if __name__ == '__main__':
    app.run_server(debug=True,port=8051)




