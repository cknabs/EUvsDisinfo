from dash.dependencies import Input, Output
from plotly import graph_objects as go

from app import app, date_language, res_content, res_social
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


# @app.callback(
#     [Output('fig-timeline', 'figure')]
# )
def update_timeline():
    sorted_dl = date_language.sum(axis=0).sort_values(ascending=False)
    top = sorted_dl.drop('Other')[:5].index

    traces = [
        go.Scatter(
            x=date_language.index, y=date_language.sum(axis=1),
            mode='lines',
            line=dict(
                dash='dot',
                color='black'
            ),
            name='Total',
        )
    ]

    traces += [
        go.Scatter(
            x=date_language.index, y=date_language[col],
            mode='lines',
            visible=True if col in top else 'legendonly',
            name=col,
        )
        for col in sorted_dl.index

    ]

    fig = go.Figure(data=traces)
    fig.update_xaxes(rangeslider_visible=True)
    return fig


@app.callback(
    Output('percentile-value', 'children'),
    [Input('percentile-slider', 'value')]
)
def update_output(value):
    percentile_value = f"Show top {int(100 * value)}% only)"
    return percentile_value
