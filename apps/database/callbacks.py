from datetime import datetime

import pandas as pd
import plotly.express as px
from dash import html
from dash.dependencies import Input, Output
from plotly import graph_objects as go

from app import app
from apps.database.data import counts_by_date, date_language, df

custom_oranges_r = ["#000000"] + px.colors.sequential.Oranges_r[:-2]


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
        autosize=True,
    )
    fig = go.Figure(data=traces, layout=layout)

    return fig


fig_map = None


def update_map():
    fig = px.choropleth(
        counts_by_date,
        animation_frame="month",
        animation_group="country",
        locations="country",
        locationmode="country names",
        color="count",
        color_continuous_scale=custom_oranges_r,
        range_color=[0, counts_by_date["count"].max()],
        scope="europe",
        labels={
            "month": "Month",
            "country": "Country/Region: ",
            "count": "Numbers of Entries",
        },
        title="Countries and Regions discussed by month",
    )

    # Update map appeareance
    fig.update_layout(
        geo=dict(
            showframe=False,
            showlakes=False,
            showcoastlines=False,
            landcolor="#000000",  # set default land color to black (to match colorscale above)
        ),
    )

    # Add dropdown to choose the scope of the map
    fig.update_layout(
        updatemenus=list(fig.layout.updatemenus)
        + [
            dict(
                buttons=list(
                    [
                        dict(
                            args=["geo.scope", "europe"],
                            label="Europe",
                            method="relayout",
                        ),
                        dict(
                            args=["geo.scope", "world"],
                            label="World",
                            method="relayout",
                        ),
                    ]
                ),
                direction="down",
                # pad={"r": 10, "t": 10},
                showactive=True,
                x=0.06,
                xanchor="left",
                y=1.006,
                yanchor="top",
            ),
        ],
        annotations=[
            dict(
                text="Scope: ",
                showarrow=False,
                x=0,
                y=1,
                yref="paper",
                align="left",
                xanchor="left",
                yanchor="top",
            )
        ],
    )

    # Speed up animation
    play_button = fig.layout.updatemenus[0].buttons[0]
    play_button.args[1]["frame"]["duration"] = 100
    play_button.args[1]["transition"]["duration"] = 1000

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
            "\u2000" * 2 + "\u000B",
            "\u2000" * 6 + "\u000B",
            "\u2000" * 12 + "\u000B",
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
