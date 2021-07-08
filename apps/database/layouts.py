import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from apps.database.callbacks import update_timeline
from apps.layouts import empty_line, header

table_header = [
    html.Thead(
        html.Tr(
            html.Th(
                [
                    dbc.Badge(
                        id="timeline-th-num_entries",
                    ),
                    " entries in ",
                    dbc.Badge(
                        id="timeline-th-language",
                    ),
                    " for ",
                    dbc.Badge(
                        id="timeline-th-date",
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

layout = [
    header,
    empty_line,
    dbc.Container(
        [empty_line, graphs], fluid=True, className="custom-container"
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
