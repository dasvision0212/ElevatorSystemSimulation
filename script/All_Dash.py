import dash
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import dash_table
import plotly.express as px

from dash.dependencies import Input, Output


### problem
### statistic => encoding, "研究大樓"為亂碼
###########  import data  #############
statistic_data = pd.read_csv('../data/statistic_df.csv', header = 0)#,encoding= 'unicode_escape'
ranked_data = pd.read_csv('../data/ranked_df.csv', header = 0)

sta_locationList = statistic_data.location.unique()
sta_policyList = statistic_data.policy.unique()
sta_dataType = statistic_data.dataType.unique()

for i in ranked_data.columns[2:]:
    ranked_data[i] = [float(format(f, '.2f').rstrip('0').rstrip('.')) for f in ranked_data[i]]

###########  end import data  #############


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Tabs(id='tabs-example', value='tab-2', children=[
        dcc.Tab(label='Single policy statistic', value='tab-1',children=[
            html.Div([
                html.H2(children='stop count & floor count'),
                html.Div([
                    html.Label('電梯組'),
                    dcc.Dropdown(
                        id="location",
                        options=[{'label': i, 'value': i} for i in sta_locationList],
                        value='研究大樓'
                    ),
                    html.Label('電梯分層政策'),
                    dcc.Dropdown(
                            id='policy',
                            options=[{'label':i, 'value':i} for i in sta_policyList],
                            value="v2-all_available"
                    )
                ],style={'width': '15%','display': 'inline-block'}),
                dcc.Graph(
                    id="GraphMeasurement"
                )
            ])
        ]),
        dcc.Tab(label='Multiple policy comparison', value='tab-2')
    ]),html.Div(id='tabs-example-content')
])

@app.callback(Output('tabs-example-content', 'children'),Input('tabs-example', 'value'))




# 'whiteSpace': 'normal',
# 'max_width':'15px',

def render_content(tab):
    if tab == 'tab-2':
        return html.Div([
                    dash_table.DataTable(
                        id='table',
                        columns=[{"name": i, "id": i} for i in ranked_data.columns],
                        style_cell={},
                        data=ranked_data.to_dict('records')
                    )
            ],style={'margin':'5% 10% 0 10%'})
        

@app.callback(Output('GraphMeasurement', 'figure'),
            [ Input('location', 'value'),
              Input('policy', 'value')])

def update_graph(location, policy):
    df = statistic_data[(statistic_data["location"] == location) & (statistic_data["policy"] == policy)]
    if len(df) == 0:
        pass
    else:
        fig = px.histogram(df, x= "data", title=location, facet_col="dataType", color="dataType")
    fig.update_layout(title_text=location)

    return fig


if __name__ == '__main__':
    app.run_server(debug=True, port=8052)