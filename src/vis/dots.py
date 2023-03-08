#!/usr/bin/env python3

import dash
from dash import Dash, dcc, html, Input, Output

import plotly.express as px

def init_vis(server, data_frames, agg_cluster_counts):
    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix="/baseline-dots/",
    )

    init_name = sorted([v for v in data_frames])[0]
    init_df = data_frames[init_name]['df']

    dash_app.layout = html.Div(children=[
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Span(
                            children="Dataset:"
                        ),
                        dcc.RadioItems(
                            [name for name in data_frames],
                            inline=True,
                            id='data-selector',
                            value=init_name
                        ),
                    ],
                    style={
                        'textAlign': 'center',
                    }
                ),
                html.Div(
                    children=[
                        html.P(
                            children="Adjust the number of clusters"
                        ),
                    ],
                    style={
                        'textAlign': 'center',
                    }
                ),
                html.Div([
                    dcc.Slider(
                        max(init_df['agg_level'].min(), init_df['agg_level'].max() - 60),
                        init_df['agg_level'].max(),
                        value=init_df['agg_level'].max() - 10,
                        step=1,
                        id='agg-slider',
                        marks=None,
                        included=False,
                    ),
                ]),
            ],
            style={
                'margin': 'auto',
                'width': '800px',
            }
        ),

        dcc.Graph(id="cluster-graph")
    ])

    # Initialize callbacks
    init_callbacks(dash_app, data_frames, agg_cluster_counts)

    return dash_app.server

def init_callbacks(dash_app, data_frames, agg_cluster_counts):
    @dash_app.callback(
        Output('agg-slider', 'min'),
        Output('agg-slider', 'max'),
        Output('agg-slider', 'value'),
        Input(component_id='data-selector', component_property='value')
    )
    def change_dataset(dataset_name):
        df = data_frames[dataset_name]['df']
        min_val = max(df['agg_level'].min(), df['agg_level'].max() - 60)
        max_val = df['agg_level'].max()
        value = df['agg_level'].max() - 10
        return min_val, max_val, value

    @dash_app.callback(
        Output(component_id='cluster-graph', component_property='figure'),
        Input(component_id='agg-slider', component_property='value'),
        Input(component_id='data-selector', component_property='value')
    )
    def update_output_div(slider_pos, dataset_name):
        df = data_frames[dataset_name]['df']
        color_map = data_frames[dataset_name]['color_map']
        filtered_df = df[df.agg_level == slider_pos]

        symbols = ["circle", "square", "diamond", "triangle-up", "triangle-down", "star", "x", "circle-open", "square-open", "diamond-open", "triangle-up-open", "triangle-down-open", "star-open", "x-open", ]
        fig = px.scatter(
            data_frame = filtered_df,
            x = 'x_vals',
            y = 'y_vals',
            custom_data = ['sentences'],
            color = 'color',
            height = 1000,
            text = 'label',
            symbol = 'marker',
            color_discrete_map = color_map,
            category_orders = {"cluster": [str(v) for v in range(agg_cluster_counts[dataset_name])]},
            labels = {"cluster": "Cluster"},
            size = 'size',
            size_max = 8,
            symbol_sequence = symbols
        )
        fig.update_traces(
            hovertemplate= "%{customdata[0]}"
        )
        fig.update_yaxes(visible=False, showticklabels=False)
        fig.update_xaxes(visible=False, showticklabels=False)

        fig.update_layout(showlegend=False)

        # Set hover style
        fig.update_layout(hovermode="closest")
        fig.update_layout(hoverdistance=50)

        # Set text labels to match color of the dots
        fig.for_each_trace(lambda t: t.update(textfont_color=t.marker.color, textposition='top center'))

        return fig
