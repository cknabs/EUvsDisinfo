from dash.dependencies import Input, Output

from app import app, res_content, res_social
from viz.util import fig_graph


@app.callback(
    [Output('fig-social', 'figure'),
     Output('fig-publishers', 'figure')],
    [Input('percentile-slider', 'value')]
)
def update_figures(value):
    percentile_cutoff = 1.0 - value
    fig_social = fig_graph(res_social, 'Publishers and Social Media Profiles', percentile_cutoff=percentile_cutoff)
    fig_publishers = fig_graph(res_content, 'Publishers', percentile_cutoff=percentile_cutoff)
    return fig_social, fig_publishers


@app.callback(
    Output('percentile-value', 'children'),
    [Input('percentile-slider', 'value')]
)
def update_output(value):
    percentile_value = f"Show top {int(100 * value)}% only)"
    return percentile_value
