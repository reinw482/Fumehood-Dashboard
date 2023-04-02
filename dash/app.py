# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import dash_treeview_antd
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import requests
import json


def create_tuple(response):
    response_data = response.json()
    response_datum = response_data[0]
    response_target = response_datum['target']
    response_datapoints = response_datum['datapoints']
    tuple_array = [tuple(x) for x in response_datapoints]
    npa = np.array(tuple_array, dtype=[
        ('value', np.double), ('ts', 'datetime64[ms]')])
    return npa


def fume_query(target, server, start, end):
    url = "https://ypsu0n34jc.execute-api.us-east-1.amazonaws.com/dev/query"
    data = {
        "range": {
            "from": start,
            "to": end,
        },
        "targets": [
            {
                "payload": {
                    "schema": server,
                },
                "target": target
            }
        ],

    }
    request = requests.post(url, json=data)
    print(request)
    # print(request.json())
    return create_tuple(request)


def query_to_list(point, server, start, end):
    master = fume_query(point, server, start, end)

    list = pd.Series(data=[i[0] for i in master], index=[i[1] for i in master])
    print("\n", point, "\n", list)

    list = list[~list.index.duplicated()]
    print("\n", point, " new\n", list)

    return list

# Arguments: Sash Point, Occ Point, Server Name, Start Time, End Time
# Returns: Total time that hood sash was open when room is unoccupied, aggregated by hour


def total_time_sash_open_unoccupied(sash_point, occ_point, server, start, end):
    sash_list = query_to_list(sash_point, server, start, end)
    occ_list = query_to_list(occ_point, server, start, end)

    df = pd.concat([sash_list, occ_list], axis=1)
    df.columns = ["sash", "occ"]

    time_interval = df.index[1].minute - df.index[0].minute

    # Figure out closed sash position
    # display(df["sash"].value_counts())

    # from running the above on a large time difference, 1.2 inches is the most common smallest value
    df["time_open_mins"] = np.where(
        (df["sash"] > 1.2) & (df["occ"] == 0), time_interval, 0)

    df = df.dropna()

    df = df.groupby(pd.Grouper(freq='60Min', label='right')).sum()

    return df["time_open_mins"]


app = Dash(__name__)

app.layout = html.Div(className="cols_wrapper", children=[
    html.Div(className="col_small", children=[
        dash_treeview_antd.TreeView(
            id='input',
            multiple=False,
            checkable=False,
            checked=['0-0-1'],
            selected=[],
            expanded=['0'],
            data={
                'title': 'Biotech',
                'key': '0',
                'children': [{
                    'title': 'Floor 1',
                    'key': '0-0',
                    'children': [
                        {'title': 'Lab 1', 'key': '0-0-1'},
                        {'title': 'Lab 2', 'key': '0-0-2'},
                        {'title': 'Lab 3', 'key': '0-0-3'},
                    ],
                }]}
        )
    ]),

    html.Div(className="col", children=[
        html.Div(className="cols_wrapper", children=[
            html.Div(className="col", children=[
                html.H1('Lab 433')
            ]),

            html.Div(className="col", children=[
                html.Label('Metric'),
                dcc.Dropdown(["BTU"],
                             "BTU", id="metric_selector"),
            ]),

            html.Div(className="col", children=[
                html.Label('Date Range'),
                dcc.Dropdown(["Last day", "Last week", "Last month"],
                             "Last week", id="date_selector"),
            ])
        ]),


        html.P("Biotech / 4th Floor / Lab 433"),

        html.Div(id='output-selected'),

        html.Div(className="cols_wrapper", children=[
            html.Div(className="col", children=[
                html.H3("Featured Rankings"),

                # TODO: Rankings box
            ]),

            html.Div(className="col", children=[
                html.H3("Graphs"),

                dcc.Loading(
                    id="is-loading",
                    children=[
                        dcc.Graph(
                            id="occ_graph",
                            # figure=fig
                        )],
                    type="circle"
                )
            ])
        ])
    ]),

])


@app.callback(Output('output-selected', 'children'),
              [Input('input', 'selected')])
def _display_selected(selected):
    return 'You have checked {}'.format(selected)


@app.callback(
    Output("occ_graph", "figure"),
    Input("date_selector", "value")
)
def update_graph(date):
    occ_data = total_time_sash_open_unoccupied(sash_point="#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/hood_sash",
                                               occ_point="#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/occ_trend",
                                               server="biotech_main",
                                               start=str(
                                                          datetime(2021, 11, 17, 1)),
                                               end=str(datetime(2021, 11, 17, 2)))
    print(occ_data)
    occ_fig = px.bar(occ_data)
    return occ_fig


if __name__ == '__main__':
    app.run_server(debug=True)
