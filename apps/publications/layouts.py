import dash_core_components as dcc
import dash_html_components as html

from apps.layouts import emptyrow, header

slider = html.Div([
    html.Div([
        html.Div(id='percentile-value'),
        dcc.Slider(id='percentile-slider',
                   min=0.01,
                   max=1,
                   step=0.01,
                   value=0.1,
                   marks={i / 100: f"{i}%" for i in range(0, 100, 10)})
    ], className='col')
], className='row')

graphs = html.Div([
    dcc.Graph(id='fig-social'),
    dcc.Graph(id='fig-publishers')
], className='col')

layout = html.Div([
    header,
    emptyrow,
    slider,
    graphs,
], className='container')
