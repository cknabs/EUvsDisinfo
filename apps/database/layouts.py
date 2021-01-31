import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from apps.database.callbacks import update_timeline
from apps.layouts import header

graphs = dbc.Col(
    children=[
        html.Div(id="selected-entries"),
        dcc.Graph(id="fig-timeline", figure=update_timeline()),
    ],
)

layout = html.Div(
    [
        header,
        graphs,
    ],
    className="container",
)

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
