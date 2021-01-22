import dash_bootstrap_components as dbc

header = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Visualisation", href="/database")),
        dbc.NavItem(dbc.NavLink("Analysis", href="/publications")),
    ],
    brand="Exploring the EUvsDisinfo database",
)
