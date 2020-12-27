import pandas as pd
from plotly import graph_objects as go

from apps.database.data import date_language


# @app.callback(
#     [Output('fig-timeline', 'figure')]
# )
def update_timeline():
    # TODO: add index to timeline
    # TODO: average over month -> get top keywords in each language for each months
    # TODO: add total as a grouped/stacked bar behind all others: see https://github.com/plotly/plotly.js/issues/4914
    sorted_dl = date_language.sum(axis=0).sort_values(ascending=False)
    total_dl = date_language.groupby(pd.Grouper(freq='M')).sum().sum(axis=1)
    top = sorted_dl[:10].index

    month_year = date_language.index.strftime('%b %Y')

    traces = [
        go.Scatter(
            x=total_dl.index.strftime('%b %Y'),
            y=total_dl,
            mode='markers',
            marker=dict(
                symbol='cross-thin',
                color='black',
                line=dict(
                    width=1,
                ),
            ),

            name='Total'
        )
    ]

    traces += [
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
        # paper_bgcolor='rgba(0,0,0,0)',
        # plot_bgcolor='rgba(0,0,0,0)',
        barmode='stack',
        yaxis=dict(
            title='Entries in the Disinfo database',
            # spikedash='dot',
            showgrid=True
        ),
        legend=dict(
            traceorder='normal'
        ),
        height=800
    )
    fig = go.Figure(data=traces, layout=layout)
    fig.update_xaxes(rangeslider_visible=True)

    return fig
