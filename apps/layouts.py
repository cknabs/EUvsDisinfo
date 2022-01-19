from datetime import datetime

import dash_bootstrap_components as dbc

from apps.database.data import df

vals = [0, 2, 1, 2, 1, 2, 2, 1, 2, 2, 3, 2, 3]
text = "eu vs disinfo"
min_x = " 2015"
max_x = " " + str(df.date.max().year)
min_y = 0
max_y = len(df.id.unique())
pos_min = 3
pos_max = 12

inner = [f"{t}|{v}" for t, v in zip(text, vals)]
inner.insert(pos_min, "[-]")
inner.insert(pos_max, "[+]")

datalegreya = f"{{{min_x}}}{''.join(inner)}{{{max_x}}}[{max_y}[{min_y}]"

padding_style = {"padding-left": "5%", "padding-right": "5%"}

header = dbc.NavbarSimple(
    dbc.Nav(
        children=[
            dbc.NavItem(dbc.NavLink("Home", href="/", active="exact")),
            dbc.NavItem(
                dbc.NavLink(
                    "Visualization", href="/visualization", active="partial"
                )
            ),
            dbc.NavItem(
                dbc.NavLink("Analysis", href="/analysis", active="partial")
            ),
        ],
        pills=False,
        navbar=True,
    ),
    brand=datalegreya,
    brand_href="/",
    fluid=True,
    className="custom-container",
    dark="True",
    color="dark",
)

empty_line = dbc.Row(className="empty-row")
