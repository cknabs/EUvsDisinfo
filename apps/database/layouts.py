import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from apps.database.callbacks import update_timeline
from apps.layouts import empty_line, header, padding_style

table_header = [
    html.Thead(
        html.Tr(
            html.Th(
                [
                    dbc.Badge(
                        id="timeline-th-num_entries",
                        style={"font-size": "100%"},
                    ),
                    " entries in ",
                    dbc.Badge(
                        id="timeline-th-language", style={"font-size": "100%"}
                    ),
                    " for ",
                    dbc.Badge(
                        id="timeline-th-date", style={"font-size": "100%"}
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
                style={"height": "100vh"},
            ),
            width=8,
        ),
        dbc.Col(
            dbc.Table(
                table_header + table_body,
                hover=True,
                responsive=True,
                striped=True,
            )
        ),
    ],
)

layout = [
    header,
    dbc.Container([empty_line, graphs], fluid=True, style=padding_style),
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
