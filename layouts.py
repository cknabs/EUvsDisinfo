import dash_core_components as dcc
import dash_html_components as html

from callbacks import update_timeline

emptyrow = html.Div([html.Div([html.Br()],
                              className='col')],
                    className='row',
                    style={'height': '50px'})

header = html.Div([
    html.Div([html.H1(children='Exploring the EUvsDisinfo database',
                      style={'textAlign': 'center'})],
             className='col'),
], className='row', )

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
    dcc.Graph(id='fig-timeline', figure=update_timeline()),
    dcc.Graph(id='fig-social'),
    dcc.Graph(id='fig-publishers')
], className='col')

main_layout = html.Div([
    header,
    emptyrow,
    slider,
    graphs,
], className='container')

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
