import pandas as pd
from plotly import graph_objects as go

from apps.database.data import date_language


# @app.callback(
#     [Output('fig-timeline', 'figure')]
# )
def update_timeline():
    # TODO: add index to timeline
    # TODO: average over month -> get top keywords in each language for each months

    sorted_dl = date_language.sum(axis=0).sort_values(ascending=False)
    total_dl = date_language.sum(axis=1)
    top = sorted_dl.drop('Other')[:5].index

    month_year = date_language.index.strftime('%b %Y')

    traces = [
        go.Bar(
            x=month_year,
            y=date_language[col],
            visible=True if col in top else 'legendonly',
            name=col,
            customdata=pd.concat([date_language.index.to_series(), date_language[col]], axis=1),
            hovertemplate='%{customdata[0]|%Y-%m-%d}: %{customdata[1]}'
        )
        for col in sorted_dl.index
    ]

    layout = go.Layout(
        title='Timeline',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        barmode='stack',
        xaxis=dict(
            tickangle=-45
        ),
    )
    fig = go.Figure(data=traces, layout=layout)
    fig.update_xaxes(rangeslider_visible=True)

    return fig
