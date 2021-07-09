import igraph as ig
import numpy as np
from dash.dependencies import Input, Output
from pandas import DataFrame
from plotly import graph_objects as go
from plotly.graph_objs import Figure

from app import app
from apps.publications.data import res_content, res_social


def fig_graph(
    data: DataFrame,
    title: str,
    percentile_cutoff: float = 0.5,
    percentile_bins: int = 100,
    color=True,
) -> Figure:
    data = data.copy()
    assert 0.0 <= percentile_cutoff <= 1.0
    assert percentile_bins > 0
    assert list(data.index) == list(data.columns)
    assert np.allclose(data.values, data.transpose().values, equal_nan=True)

    diag = data.values.diagonal().copy()
    np.fill_diagonal(data.values, np.nan)
    print(f"Creating figure for dataframe of shape {data.shape}")

    drop_labels = data[
        data.sum().rank(method="first", pct=True) <= percentile_cutoff
    ].index
    print(f"\t{percentile_cutoff=}, dropping {len(drop_labels)} entries")
    data.drop(drop_labels, axis=0, inplace=True)
    data.drop(drop_labels, axis=1, inplace=True)

    G = ig.Graph.Adjacency(
        np.where(
            np.logical_and(
                np.isfinite(data.values), np.greater(data.values, 0)
            ),
            True,
            False,
        ).tolist(),
        mode=ig.ADJ_UNDIRECTED,
    )

    # clustering = G.community_fastgreedy().as_clustering()
    # G = clustering.graph
    # clusters = clustering.membership

    # layout = G.layout('sphere', dim=3)
    layout = G.layout_auto(dim=3)
    x_n, y_n, z_n = list(zip(*layout))

    min_size, max_size = 5, 10  # in px
    if data.shape[0] > 1:
        sizes = diag
        sizes /= sizes.max()  # in [0, 1]
        sizes = (
            min_size + (max_size - min_size) * sizes
        )  # in [min_size, max_size]
    else:
        sizes = [max_size for _ in range(data.shape[0])]

    weights = list(
        data.fillna(0).values[e.source][e.target].item() for e in G.es
    )
    if len(weights) > 0:
        centralities = np.array(G.betweenness(weights=weights))
        if centralities.min() != centralities.max():
            centralities = (centralities - centralities.min()) / (
                centralities.max() - centralities.min()
            )
    else:
        centralities = []

    node_trace = go.Scatter3d(
        x=x_n,
        y=y_n,
        z=z_n,
        mode="markers+text",
        marker=dict(
            size=sizes,
            sizemode="diameter",
            color=centralities if color else None,
            opacity=1,
            colorscale="Jet",
            colorbar=dict(title="vertex betweenness", thickness=5)
            if color
            else None,
        ),
        hovertext=data.columns,
        hoverinfo="text",
        hoverlabel=dict(bgcolor="white"),
        showlegend=False,
    )
    print(f"\tcreated scatter plot with {len(x_n)} nodes")

    percentiles = (
        data.unstack()
        .rank(method="first", pct=True)
        .values.reshape(data.shape)
    )
    x_e = {i: [] for i in range(percentile_bins)}
    y_e = {i: [] for i in range(percentile_bins)}
    z_e = {i: [] for i in range(percentile_bins)}

    min_width, max_width = min_size / 2, max_size / 2  # in px
    linspace_width = np.linspace(min_width, max_width, num=percentile_bins)
    w_e = dict(enumerate(linspace_width))

    min_alpha, max_alpha = 0.01, 0.2
    linspace_alpha = np.linspace(min_alpha, max_alpha, num=percentile_bins)
    a_e = dict(enumerate(linspace_alpha))

    quantiles = []
    for e in G.es:
        s = e.source
        t = e.target
        quantile = min(
            percentile_bins - 1, int(percentile_bins * percentiles[s][t])
        )
        quantiles.append(quantile)
        x_e[quantile] += [layout[s][0], layout[t][0], None]
        y_e[quantile] += [layout[s][1], layout[t][1], None]
        z_e[quantile] += [layout[s][2], layout[t][2], None]

    edge_traces = [
        go.Scatter3d(
            x=x_e[i],
            y=y_e[i],
            z=z_e[i],
            mode="lines",
            line=dict(width=w_e[i], color=f"rgba(0,0,0,{a_e[i]})"),
            showlegend=False,
            hoverinfo="none",
        )
        for i in range(percentile_bins)
    ]
    print(
        f"\tcreated scatter plot with {len(G.es)} edges across {percentile_bins} bins"
    )

    layout = go.Layout(
        title=title,
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
        ),
        hovermode="closest",
    )

    fig = go.Figure(data=edge_traces + [node_trace], layout=layout)
    return fig


def fig_graph_socials(
    data: DataFrame,
    title: str,
    percentile_cutoff: float = 0.5,
    percentile_bins: int = 100,
) -> Figure:
    data = data.copy()
    assert 0.0 <= percentile_cutoff <= 1.0
    assert percentile_bins > 0
    assert list(data.index) == list(data.columns)
    assert np.allclose(data.values, data.transpose().values, equal_nan=True)

    diag = data.values.diagonal().copy()
    np.fill_diagonal(data.values, np.nan)
    print(f"Creating figure for dataframe of shape {data.shape}")

    drop_labels = data[
        data.sum().rank(method="first", pct=True) <= percentile_cutoff
    ].index
    print(f"\t{percentile_cutoff=}, dropping {len(drop_labels)} entries")
    data.drop(drop_labels, axis=0, inplace=True)
    data.drop(drop_labels, axis=1, inplace=True)

    G = ig.Graph.Adjacency(
        np.where(
            np.logical_and(
                np.isfinite(data.values), np.greater(data.values, 0)
            ),
            True,
            False,
        ).tolist(),
        mode=ig.ADJ_UNDIRECTED,
    )

    # clustering = G.community_fastgreedy().as_clustering()
    # G = clustering.graph
    # clusters = clustering.membership

    # layout = G.layout('sphere', dim=3)
    layout = G.layout_auto(dim=3)
    x_n, y_n, z_n = list(zip(*layout))

    min_size, max_size = 5, 10  # in px
    if data.shape[0] > 1:
        sizes = diag
        sizes /= sizes.max()  # in [0, 1]
        sizes = (
            min_size + (max_size - min_size) * sizes
        )  # in [min_size, max_size]
    else:
        sizes = [max_size for _ in range(data.shape[0])]

    def get_color_from_name(s):
        # TODO: very inefficient and error-prone, rather use the fields parsed in data.py instead
        facebook = "#3b5998"
        youtube = "#e52d27"
        twitter = "#55acee"
        web = "gray"

        if s.startswith("@") or (s.startswith("http") and "twitter.com" in s):
            return twitter
        elif s.startswith("http") and "facebook.com" in s:
            return facebook
        elif s.startswith("http") and "youtube.com" in s:
            return youtube
        else:
            return web

    colors = [get_color_from_name(s) for s in data.columns]

    node_trace = go.Scatter3d(
        x=x_n,
        y=y_n,
        z=z_n,
        mode="markers+text",
        marker=dict(
            size=10 * sizes,
            sizemode="area",
            color=colors,
            opacity=1,
        ),
        hovertext=data.columns,
        hoverinfo="text",
        hoverlabel=dict(bgcolor="white"),
        showlegend=False,
    )
    print(f"\tcreated scatter plot with {len(x_n)} nodes")

    percentiles = (
        data.unstack()
        .rank(method="first", pct=True)
        .values.reshape(data.shape)
    )
    x_e = {i: [] for i in range(percentile_bins)}
    y_e = {i: [] for i in range(percentile_bins)}
    z_e = {i: [] for i in range(percentile_bins)}

    min_width, max_width = min_size / 2, max_size / 2  # in px
    linspace_width = np.linspace(min_width, max_width, num=percentile_bins)
    w_e = dict(enumerate(linspace_width))

    min_alpha, max_alpha = 0.01, 0.2
    linspace_alpha = np.linspace(min_alpha, max_alpha, num=percentile_bins)
    a_e = dict(enumerate(linspace_alpha))

    quantiles = []
    for e in G.es:
        s = e.source
        t = e.target
        quantile = min(
            percentile_bins - 1, int(percentile_bins * percentiles[s][t])
        )
        quantiles.append(quantile)
        x_e[quantile] += [layout[s][0], layout[t][0], None]
        y_e[quantile] += [layout[s][1], layout[t][1], None]
        z_e[quantile] += [layout[s][2], layout[t][2], None]

    edge_traces = [
        go.Scatter3d(
            x=x_e[i],
            y=y_e[i],
            z=z_e[i],
            mode="lines",
            line=dict(width=w_e[i], color=f"rgba(0,0,0,{a_e[i]})"),
            showlegend=False,
            hoverinfo="none",
        )
        for i in range(percentile_bins)
    ]
    print(
        f"\tcreated scatter plot with {len(G.es)} edges across {percentile_bins} bins"
    )

    layout = go.Layout(
        title=title,
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
        ),
        hovermode="closest",
    )
    # TODO: add legend

    fig = go.Figure(data=edge_traces + [node_trace], layout=layout)
    return fig


@app.callback(
    Output("fig-publishers", "figure"),
    [Input("percentile-slider", "value")],
)
def update_figures(value):
    percentile_cutoff = 1.0 - value
    fig_publishers = fig_graph(
        res_content, "Publishers", percentile_cutoff=percentile_cutoff
    )
    return fig_publishers


@app.callback(
    Output("percentile-value", "children"),
    [Input("percentile-slider", "value")],
)
def update_output(value):
    percentile_value = f"Show top {int(100 * value)}% of all publishers"
    return percentile_value
