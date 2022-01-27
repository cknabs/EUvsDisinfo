import dash_bootstrap_components as dbc
from dash import dcc, html

from apps.database.callbacks import update_heatmap, update_map, update_timeline
from apps.layouts import empty_line, header

table_header = [
    html.Thead(
        html.Tr(
            html.Th(
                [
                    dbc.Badge(
                        id="timeline-th-num_entries",
                        children="\u2000" * 2 + "\u000B",
                    ),
                    " entries in ",
                    dbc.Badge(
                        id="timeline-th-language",
                        children="\u2000" * 6 + "\u000B",
                    ),
                    " for ",
                    dbc.Badge(
                        id="timeline-th-date",
                        children="\u2000" * 12 + "\u000B",
                    ),
                ]
            )
        )
    )
]

table_body = [html.Tbody(id="timeline-tbody")]

graphs = dbc.Row(
    [
        dbc.Col(
            dcc.Graph(
                id="fig-timeline",
                figure=update_timeline(),
                style=dict(height="100%"),
            ),
            width=8,
        ),
        dbc.Col(
            dbc.Table(
                table_header + table_body,
                hover=True,
                responsive=True,
                striped=True,
            ),
            id="col-db-table",
        ),
    ],
    className="full-height",
)

map = dbc.Row(
    [
        dbc.Col(
            dcc.Markdown(),
            id="descr-map",
        ),
        dbc.Col(
            children=[
                dcc.Graph(
                    id="fig-map",
                    figure=update_map(),
                    style=dict(height="100%"),
                )
            ],
            width=8,
        ),
    ],
    className="full-height",
)

heatmaps = dbc.Row(
    [
        dbc.Col(
            children=[
                dcc.Graph(
                    id="fig-heatmap",
                    figure=update_heatmap(),
                    style=dict(height="100%"),
                )
            ],
            width=8,
        ),
        dbc.Col(
            dcc.Markdown(),
            id="descr-heatmap",
        ),
    ],
    className="full-height",
)

layout = [
    header,
    empty_line,
    dbc.Container(
        [empty_line, graphs], fluid=True, className="custom-container"
    ),
    dbc.Container([empty_line, map], fluid=True, className="custom-container"),
    dbc.Container(
        [empty_line, heatmaps], fluid=True, className="custom-container"
    ),
]

# html.Div(children=[
#     html.H1(children=),
#     html.Div(style=dict(width='20%', display='inline-block'),
#              children=[
#
#              ]),
#     html.Div(style=dict(width='40%', display='inline-block'),
#              children=[
#                  dcc.Graph(id='fig-social'),  # , figure=fig_social),
#              ]),
#     html.Div(
#         dcc.Graph(id='fig-publishers'),  # , figure=fig_content),
#         style=dict(width='40%', display='inline-block')
#     )
# ])
