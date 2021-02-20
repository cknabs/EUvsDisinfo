import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import apps
from app import app

# from apps.database.layouts import layout as database_layout
# from apps.publications.layouts import layout as publications_layout

app.layout = html.Div(
    [dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
)


# Load page dynamically
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/":
        return "TODO"
    if pathname == "/visualization":
        return apps.database.layout
    elif pathname == "/analysis":
        return apps.publications.layout
    else:
        return "404"


server = app.server
if __name__ == "__main__":
    app.run_server(debug=True)
