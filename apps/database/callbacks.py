from datetime import datetime

import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output
from plotly import graph_objects as go

from app import app
from apps.database.data import date_language, df


# @app.callback(
#     [Output('fig-timeline', 'figure')]
# )
def update_timeline():
    # TODO: average over month -> get top keywords in each language for each months
    # TODO: add total as a grouped/stacked bar behind all others: see https://github.com/plotly/plotly.js/issues/4914
    sorted_dl = date_language.sum(axis=0).sort_values(ascending=False)
    total_dl = date_language.groupby(pd.Grouper(freq="M")).sum().sum(axis=1)
    top = sorted_dl[:10].index

    month_year = date_language.index.strftime("%b %Y")

    traces = [
        go.Scatter(
            x=total_dl.index.strftime("%b %Y"),
            y=total_dl,
            mode="markers",
            marker=dict(
                symbol="cross-thin",
                color="black",
                line=dict(
                    width=1,
                ),
            ),
            name="Total",
        )
    ]

    traces += [
        go.Bar(
            x=month_year,
            y=date_language[col],
            visible=True if col in top else "legendonly",
            name=col,
            customdata=pd.concat(
                [
                    date_language.index.to_series(),
                    date_language[col],
                    pd.Series(
                        [col] * len(date_language.index),
                        index=date_language.index,
                    ),
                ],
                axis=1,
            ),
            hovertemplate="%{customdata[0]|%Y-%m-%d}: %{customdata[1]}",
        )
        for col in sorted_dl.index
    ]

    layout = go.Layout(
        title="Entries in the EUvsDisinfo database by date of publication",
        # paper_bgcolor='rgba(0,0,0,0)',
        # plot_bgcolor='rgba(0,0,0,0)',
        barmode="stack",
        yaxis=dict(
            title="Entries in the Disinfo database",
            # spikedash='dot',
            showgrid=True,
        ),
        legend=dict(traceorder="normal"),
    )
    fig = go.Figure(data=traces, layout=layout)

    return fig


@app.callback(
    [
        Output("timeline-th-num_entries", "children"),
        Output("timeline-th-language", "children"),
        Output("timeline-th-date", "children"),
        Output("timeline-tbody", "children"),
    ],
    [Input("fig-timeline", "clickData")],
)
def update_selected_entries(click_data):
    if click_data is None:
        return (
            "\t",
            "\t",
            "\t",
            [
                html.Tr(
                    html.Td(
                        "Click on a bar in the chart to see which entries were published on the selected day in the selected language. "
                    )
                )
            ],
        )
    point = click_data["points"][0]
    date, num_entries, language = point["customdata"]
    entries = df.loc[date]  # entries from same day
    entries = entries[
        entries["language"] == language
    ]  # entries with same language

    date_obj = datetime.fromisoformat(date)

    table_body = [
        html.Tr(
            html.Td(
                html.A(
                    title,
                    href=entry_id,
                    target="_blank",
                    rel="noreferrer noopener",
                )
            )
        )
        for title, entry_id in zip(entries["title"], entries["id"])
    ]

    return num_entries, language, date_obj.strftime("%h %d, %Y"), table_body
