import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from apps.layouts import header

slider = dbc.Row(
    children=[
        dbc.Col(
            [
                html.Div(id="percentile-value"),
                dcc.Slider(
                    id="percentile-slider",
                    min=0.01,
                    max=1,
                    step=0.01,
                    value=0.1,
                    marks={i / 100: f"{i}%" for i in range(0, 100, 10)},
                ),
            ]
        )
    ],
)

graphs = dbc.Col(
    [dcc.Graph(id="fig-social"), dcc.Graph(id="fig-publishers")],
)

layout = [
    header,
    dbc.Container(
        [
            slider,
            graphs
        ], className="custom-container")
]
