import dash_bootstrap_components as dbc
import dash_html_components as html

# TODO: generate the following from the actual data
vals = [0, 2, 1, 2, 1, 2, 2, 1, 2, 2, 3, 2, 3]
text = "eu vs disinfo"
min_x = " 2015"
max_x = " 2021"
min_y = 0
max_y = 10000
pos_min = 3
pos_max = 12

inner = [f"{t}|{v}" for t, v in zip(text, vals)]
inner.insert(pos_min, "[-]")
inner.insert(pos_max, "[+]")

datalegreya = f"{{{min_x}}}{''.join(inner)}{{{max_x}}}[{max_y}[{min_y}]"

title = [
    "Exploring the ",
    html.Span(
        children=datalegreya, style={"font-size": "200%", "padding": "0.25em"}
    ),
    " database",
]
header = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Visualisation", href="/database")),
        dbc.NavItem(dbc.NavLink("Analysis", href="/publications")),
    ],
    brand=datalegreya,  # "Exploring the EUvsDisinfo database",
    brand_style={"font-family": "Datalegreya-Gradient", "font-size": "400%"},
)
