from datetime import datetime

import pandas as pd
import plotly.express as px
from dash import html
from dash.dependencies import Input, Output
from plotly import graph_objects as go

from app import app
from apps.database.data import date_language, df

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


def update_map():
    def to_month(x):
        return datetime.strftime(x, "%Y-%m")

    counts_by_date = (
        df[["date", "country"]]
        .reset_index(drop=True)
        .value_counts()
        .reset_index()
        .rename(columns={0: "count"})
    )
    counts_by_date["month"] = counts_by_date["date"].map(to_month)
    counts_by_date = counts_by_date.drop(columns=["date"]).sort_values(
        by="month"
    )

    all_months = (
        pd.date_range(
            counts_by_date["month"].min(),
            counts_by_date["month"].max(),
            freq="M",
        )
        .map(to_month)
        .to_frame(index=False, name="month")
    )
    all_countries = pd.Series(
        counts_by_date["country"].unique(), name="country"
    ).to_frame()
    fill_vals = pd.merge(all_months, all_countries, how="cross")
    fill_vals["count"] = 0

    counts_by_date = (
        pd.concat([counts_by_date, fill_vals])
        .drop_duplicates(keep="first")
        .sort_values(by="month")
    )

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
    )

    fig.update_layout(
        geo=dict(
            showframe=False,
            showlakes=False,
            showcoastlines=False,
            landcolor="#000000",  # set default land color to black (to match colorscale above)
        ),
    )

    # Speed up animation
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 50
    fig.layout.updatemenus[0].buttons[0].args[1]["transition"][
        "duration"
    ] = 100

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
