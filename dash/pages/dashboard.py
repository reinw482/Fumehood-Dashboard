import dash
from dash import Dash, html, dcc, Input, Output, callback, clientside_callback
import dash_bootstrap_components as dbc
import dash_treeview_antd
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import requests
import json

app = Dash(__name__)

dash.register_page(__name__)


def layout(building=None, floor=None, lab=None, **other_unknown_query_strings):
    return html.Div(className="cols_wrapper", children=[
        # dcc.Location(id='url', refresh=False),  # URL location component

        dbc.Row([
            dbc.Col([
                dash_treeview_antd.TreeView(
                    id='input',
                    multiple=False,
                    checkable=False,
                    checked=[],
                    selected=[],
                    expanded=["?building=biotech"],
                    data={
                        'title': 'Biotech',
                        'key': '?building=biotech',
                        'children': [{
                            'title': 'Floor 1',
                            'key': '?building=biotech&floor=1',
                            'children': [
                                {'title': 'Lab 1',
                                 'key': '?building=biotech&floor=1&lab=1'},
                                {'title': 'Lab 2',
                                 'key': '?building=biotech&floor=1&lab=2'},
                                {'title': 'Lab 3',
                                 'key': '?building=biotech&floor=1&lab=3'},
                            ],
                        }]}
                )
            ], width=3),

            dbc.Col([
                dbc.Row([
                    dbc.Col([
                        html.H1(', '.join(filter(None, (building, floor, lab))))
                    ]),
                    dbc.Col([
                        html.Label('Metric'),
                        dcc.Dropdown(["BTU"],
                                     "BTU", id="metric_selector")
                    ]),
                    dbc.Col([
                        html.Label('Date Range'),
                        dcc.Dropdown(["Last day", "Last week", "Last month"],
                                     "Last week", id="date_selector")
                    ])
                ]),

                dbc.Row([
                    dbc.Col([
                        html.H3("Featured Rankings"),
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H4("3rd Best",
                                                className="card-title"),
                                        html.H6("On Olin Floor 3"),
                                        html.P(
                                            "For least avg. energy when unoccupied (2000 BTU/hr)",
                                            className="card-text",
                                        )
                                    ]
                                ),
                            ], className="mb-2"),

                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H4("1st Best",
                                                className="card-title"),
                                        html.H6("On Olin Floor 3"),
                                        html.P(
                                            "For Least avg. time open when unoccupied (0 min/hr)",
                                            className="card-text",
                                        )
                                    ]
                                ),
                            ])
                    ]),
                    dbc.Col([
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
                    ]),
                ])

            ])
        ]),

        html.Div(id='output-selected') # Need this to do the page click callback for some reason!
    ])

# @callback(Output('title', 'children'),
#               [Input('input', 'selected')])
# def update_title(selected):
#     if selected:
#         selected_item = selected[0]  # Assuming single selection
#         return selected_item
#     else:
#         return 'Biotech' # Default value


# @callback(Output('breadcrumb', 'children'),
#               [Input('input', 'selected')])
# def update_breadcrumb(selected):
#     if selected:
#         selected_item = selected[0]  # Assuming single selection

#         if selected_item == 'Biotech':
#             breadcrumb_text = html.A('Biotech', href='/biotech')
#         elif selected_item == 'Floor 1':
#             breadcrumb_text = html.A('Biotech', href='/biotech'), ' / ', html.A('Floor 1', href='/floor1')
#         else:
#             breadcrumb_text = html.A('Biotech', href='/biotech'), ' / ', html.A('Floor 1', href='/floor1'), ' / ', html.A(selected_item, href='/' + selected_item)

#         return html.P(breadcrumb_text)
#     else:
#         breadcrumb_text = html.A('Biotech', href='/biotech')  # Default value
#         return html.P(breadcrumb_text)


# @app.callback(Output("url", "pathname"), [Input("input", "selected_item")])
# def update_url_path(selected_item):
#     if selected_item is not None:
#         print("/" + selected_item["value"])
#         return "/" + selected_item["value"]
#     return "/"


# @app.callback(Output("page-info", "children"), [Input("url", "pathname")])
# def update_page_content(pathname):
#     if pathname:
#         # extract floor number and lab number from URL path
#         parts = pathname.split("/")
#         floor = parts[1].replace("floor", "")
#         lab = parts[2].replace("lab", "")

#         # logic to fetch and display information based on URL path
#         floor_info = f"Floor Number: {floor}"
#         lab_info = f"Lab Number: {lab}"

#         return html.Div(
#             children=[
#                 html.P(floor_info),
#                 html.P(lab_info),
#             ],
#         )
#     return ""


# @app.callback(Output('output-selected', 'children'),
#               [Input('input', 'selected')])
# def _display_selected(selected):
#     return 'You have checked {}'.format(selected)

clientside_callback(
    """
    function(input) {
        console.log(input[0]);
        window.open(`/pages/dashboard${input[0]}`, "_self");
        return input[0];
    }
    """,
    Output('output-selected', 'children'),
    Input('input', 'selected'), prevent_initial_call=True
)


@callback(
    Output("occ_graph", "figure"),
    Input("date_selector", "value")
)
def update_graph(date):
    print("hi")

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

        list = pd.Series(data=[i[0] for i in master],
                         index=[i[1] for i in master])
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

    occ_data = total_time_sash_open_unoccupied(sash_point="#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/hood_sash",
                                               occ_point="#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/occ_trend",
                                               server="biotech_main",
                                               start=str(
                                                   datetime(2021, 11, 17, 1)),
                                               end=str(datetime(2021, 11, 17, 2)))
    print(occ_data)
    occ_fig = px.bar(occ_data,
                      labels={
        "value": "Minutes Open",
        "index": "Date and Time",
        "variable": ""},
        title="Time Sash Open When Room Unoccupied")

    return occ_fig

# if __name__ == '__main__':
#     app.run_server(debug=True)