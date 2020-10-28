import numpy as np
import plotly.graph_objects as go
from pandas import DataFrame
import igraph as ig


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


def plot_graph(data: DataFrame, percentile_cutoff: float = 0.5, percentile_bins: int = 100):
    # https://plotly.com/python/v3/3d-network-graph/
    # https://towardsdatascience.com/python-interactive-network-visualization-using-networkx-plotly-and-dash-e44749161ed7
    # https://plotly.com/python/network-graphs/#create-network-graph
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

    SCALE = 1
    # layout = G.layout('sphere', dim=3)
    layout = G.layout_auto(dim=3)
    Xn, Yn, Zn = list(zip(*layout))
    Xn = tuple(map(lambda x: SCALE * x, Xn))
    Yn = tuple(map(lambda x: SCALE * x, Yn))
    Zn = tuple(map(lambda x: SCALE * x, Zn))

    min_size, max_size = 2, 20  # in px
    sizes = data.sum(axis=0)
    sizes /= sizes.max()  # in [0, 1]
    sizes = min_size + (max_size - min_size) * sizes  # in [min_size, max_size]

    node_trace = go.Scatter3d(
        x=Xn, y=Yn, z=Zn,
        mode='markers+text',
        marker=dict(
            size=sizes,
            color=data.sum(axis=0),
            colorscale='Jet'
        ),
        hovertext=data.columns,
        hoverinfo='text',
        hoverlabel=dict(
            bgcolor='white'
        )
    )

    # clustering = G.community_fastgreedy().as_clustering()
    # G = clustering.graph
    # clusters = clustering.membership

    percentiles = data.unstack().rank(method='first', pct=True).values.reshape(data.shape)
    Xe = {i: [] for i in range(percentile_bins)}
    Ye = {i: [] for i in range(percentile_bins)}
    Ze = {i: [] for i in range(percentile_bins)}

    def interpolate(val: float, min_val: float, max_val: float) -> float:
        assert 0.0 <= val <= 1.0
        return

    def get_width(val):

        return min_width + (max_width - min_width) * val / (percentile_bins - 1)
        # if val < k / 2:
        #     return 0
        # else:
        #     val = 2 * (val - k / 2)
        #     return min_width + (max_width - min_width) * val / (k - 1)

    def get_alpha(val):

        if val <= percentile_bins / 2:
            return min_alpha
        else:
            val = (val - 1 - percentile_bins / 2) / (percentile_bins / 2 - 2)
            return min_alpha + (max_alpha - min_alpha) * val

    min_width, max_width = 0, 5  # in px
    linspace_width = np.linspace(min_width, max_width, num=percentile_bins)
    We = dict(enumerate(linspace_width))

    min_alpha, max_alpha = 0.01, 0.2
    linspace_alpha = np.linspace(min_alpha, max_alpha, num=percentile_bins)
    Ae = dict(enumerate(linspace_alpha))

    traces = []
    quantiles = []
    for e in G.es:
        s = e.source
        t = e.target
        quantile = min(percentile_bins - 1, int(percentile_bins * percentiles[s][t]))
        quantiles.append(quantile)
        Xe[quantile] += [SCALE * layout[s][0], SCALE * layout[t][0], None]
        Ye[quantile] += [SCALE * layout[s][1], SCALE * layout[t][1], None]
        Ze[quantile] += [SCALE * layout[s][2], SCALE * layout[t][2], None]

    for i in range(percentile_bins):
        if We[i] > 0:
            traces.append(go.Scatter3d(
                x=Xe[i], y=Ye[i], z=Ze[i],
                mode='lines',
                line=dict(
                    width=We[i],
                    color=f'rgba(0,0,0,{Ae[i]})'
                ),
                showlegend=False,
                hoverinfo='none'
            ))

    layout = go.Layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False)
        )
    )

    fig = go.Figure(
        data=traces + [node_trace],
        layout=layout
    )
    fig.show()
