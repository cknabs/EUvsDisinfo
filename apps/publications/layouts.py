from pathlib import Path

import dash_bootstrap_components as dbc
from dash import dcc, html

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

curr_dir = Path(__file__).resolve().parent

with open(curr_dir / "publishers-socials.md", "r") as fig_social_md_file:
    fig_social_md = fig_social_md_file.read()
fig_social_text = dcc.Markdown(children=fig_social_md)

containers = [
    dbc.Container(
        dbc.Row(
            [
                fig_social_text,
                dcc.Loading(dcc.Graph(id="fig-social"), id="loading-social"),
            ]
        ),
        className="full-height",
    ),
    dbc.Container(
        [slider, dcc.Loading(dbc.Row(dcc.Graph(id="fig-publishers")))],
        className="full-height",
    ),
]

layout = [header, dbc.Container(containers, className="custom-container")]
