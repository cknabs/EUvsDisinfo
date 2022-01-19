from pathlib import Path

import dash_bootstrap_components as dbc
from dash import dcc

from apps.layouts import empty_line, header

curr_dir = Path(__file__).resolve().parent

with open(curr_dir / "home.md", "r") as home_md_file:
    home_md = home_md_file.read()
home_text = dcc.Markdown(children=home_md)

layout = [
    header,
    empty_line,
    dbc.Container(
        [home_text],
        className="custom-container",
    ),
]
