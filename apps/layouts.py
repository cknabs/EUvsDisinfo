import dash_core_components as dcc
import dash_html_components as html

emptyrow = html.Div(
    [html.Div([html.Br()], className="col")],
    className="row",
    style={"height": "50px"},
)

header = html.Div(
    [
        html.Div(
            [
                html.H1(
                    children="Exploring the EUvsDisinfo database",
                    style={"textAlign": "center"},
                )
            ],
            className="col",
        ),
    ],
    className="row",
)
