import igraph as ig
import numpy as np
import plotly.graph_objects as go
from pandas import DataFrame
from plotly.graph_objs import Figure


def explode_replace(data: DataFrame, old_name: str, new_name: str):
    # data[old_name] = data[old_name].str.split('+')
    data = data.explode(old_name)
    data = data.rename(columns={old_name: new_name})
    return data


def split(data: DataFrame, column: str, fill_na=None):
    res = data[column].str.split('+')
    if fill_na is not None:
        res.fillna('', inplace=True)
    return res


def sort(data: DataFrame) -> DataFrame:
    """Sort the rows and columns of :param data: by the sum of the row/column, using the row/column name to break ties.
    """
    # Compute sums of row/column
    sum_of_rows = data.sum(axis='columns')
    sum_of_cols = data.sum(axis='index')
    data['sum_of_rows'] = sum_of_rows
    data.loc['sum_of_cols'] = sum_of_cols
    # Use MergeSort, which is a stable sorting algorithm
    return data \
        .sort_index(axis='index') \
        .sort_index(axis='columns', kind='mergesort') \
        .sort_values(by='sum_of_rows', ascending=False, axis='index', kind='mergesort') \
        .drop('sum_of_rows', axis='columns') \
        .sort_values(by='sum_of_cols', ascending=False, axis='columns', kind='mergesort') \
        .drop('sum_of_cols', axis='index')


def plot_sankey(data: DataFrame, min_val: int = 50):
    labels, sources, targets, values = [], [], [], []
    labels = list(data.index) + list(data.columns)
    idx = {name: i for i, name in enumerate(labels)}

    for index, row in data.iterrows():
        if len(index) == 0:
            continue
        for col, val in row.iteritems():
            if len(col) == 0:
                continue
            if val > min_val:
                sources.append(idx[index])
                targets.append(idx[col])
                values.append(val)

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            label=labels,
            color='black'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color='gray'
        ),
        orientation='h'
    )])
    fig.show()


def plot_raw(data: DataFrame):
    np.fill_diagonal(data.values, np.nan)
    import plotly.express as px
    fig = px.imshow(data)
    fig.show()


def fig_graph(data: DataFrame, trace_name: str, percentile_cutoff: float = 0.5, percentile_bins: int = 100) -> Figure:
    assert 0.0 <= percentile_cutoff <= 1.0
    assert percentile_bins > 0
    assert list(data.index) == list(data.columns)
    assert np.allclose(data.values, data.transpose().values, equal_nan=True)

    np.fill_diagonal(data.values, np.nan)

    drop_labels = data[data.sum().rank(method='first', pct=True) <= percentile_cutoff].index
    data.drop(drop_labels, axis=0, inplace=True)
    data.drop(drop_labels, axis=1, inplace=True)

    G = ig.Graph.Adjacency(
        np.where(np.isfinite(data.values), True, False).tolist(),
        mode=ig.ADJ_UNDIRECTED
    )

    # clustering = G.community_fastgreedy().as_clustering()
    # G = clustering.graph
    # clusters = clustering.membership

    # layout = G.layout('sphere', dim=3)
    layout = G.layout_auto(dim=3)
    x_n, y_n, z_n = list(zip(*layout))

    min_size, max_size = 5, 10  # in px
    sizes = data.sum(axis=0)
    sizes /= sizes.max()  # in [0, 1]
    sizes = min_size + (max_size - min_size) * sizes  # in [min_size, max_size]

    centralities = np.array(G.betweenness())
    centralities = (centralities - centralities.min()) / (centralities.max() - centralities.min())

    node_trace = go.Scatter3d(
        x=x_n, y=y_n, z=z_n,
        mode='markers+text',
        marker=dict(
            size=sizes,
            sizemode='diameter',
            color=centralities,
            opacity=1,
            colorscale='Jet',
            colorbar=dict(
                title='vertex betweenness',
                thickness=5
            )
        ),
        hovertext=data.columns,
        hoverinfo='text',
        hoverlabel=dict(
            bgcolor='white'
        ),
        name=trace_name,
    )

    percentiles = data.unstack().rank(method='first', pct=True).values.reshape(data.shape)
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
        quantile = min(percentile_bins - 1, int(percentile_bins * percentiles[s][t]))
        quantiles.append(quantile)
        x_e[quantile] += [layout[s][0], layout[t][0], None]
        y_e[quantile] += [layout[s][1], layout[t][1], None]
        z_e[quantile] += [layout[s][2], layout[t][2], None]

    edge_traces = [
        go.Scatter3d(
            x=x_e[i], y=y_e[i], z=z_e[i],
            mode='lines',
            line=dict(
                width=w_e[i],
                color=f'rgba(0,0,0,{a_e[i]})'
            ),
            showlegend=False,
            hoverinfo='none'
        )
        for i in range(percentile_bins)
    ]

    layout = go.Layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False)
        ),
        hovermode='closest'
    )

    fig = go.Figure(
        data=edge_traces + [node_trace],
        layout=layout
    )
    return fig
