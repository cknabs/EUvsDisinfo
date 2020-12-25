from plotly import graph_objects as go
from scipy import signal

from apps.database.data import date_language


# @app.callback(
#     [Output('fig-timeline', 'figure')]
# )
def update_timeline():
    # TODO: add index to timeline
    # TODO: average over week -> get top keywords in each language for each week
    sorted_dl = date_language.sum(axis=0).sort_values(ascending=False)
    total_dl = date_language.sum(axis=1)
    # smoothed_dl = signal.savgol_filter(date_language, window_length=7, polyorder=3)
    smoothed_total_dl = signal.savgol_filter(total_dl, window_length=31, polyorder=3)
    top = sorted_dl.drop('Other')[:5].index

    traces = [
        go.Scatter(
            x=date_language.index, y=smoothed_total_dl,
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
            x=date_language.index, y=signal.savgol_filter(date_language[col], window_length=31, polyorder=3),
            mode='lines',
            visible=True if col in top else 'legendonly',
            name=col,
        )
        for col in sorted_dl.index
    ]

    layout = go.Layout(
        title='Timeline',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    fig = go.Figure(data=traces, layout=layout)
    fig.update_xaxes(rangeslider_visible=True)
    return fig
