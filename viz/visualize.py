import igraph as ig
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pandas import DataFrame
from plotly.subplots import make_subplots
from sklearn.manifold import SpectralEmbedding
from sklearn.preprocessing import MultiLabelBinarizer

from analysis.cooccurrence import CoOccurrence
from viz.util import sort, split


def plot_marginal(data: DataFrame):
    sum_of_rows = data.sum(axis='columns')
    sum_of_cols = data.sum(axis='index')
    data['sum_of_rows'] = sum_of_rows
    data.loc['sum_of_cols'] = sum_of_cols
    data = data.sort_values(by='sum_of_rows', ascending=False, axis='index') \
        .sort_values(by='sum_of_cols', ascending=False, axis='columns')
    fig = make_subplots(rows=2, cols=2,
                        row_heights=[0.2, 0.8], column_width=[0.8, 0.2],
                        vertical_spacing=0.01, horizontal_spacing=0.01
                        )
    fig.update_layout(template='plotly_dark')

    colorscale = 'solar'

    fig.add_trace(go.Bar(y=data.transpose()['sum_of_cols'],
                         x=data.columns[:-1],
                         showlegend=False,
                         marker=dict(color=data.transpose()['sum_of_cols'], colorscale=colorscale)),
                  row=1, col=1)
    fig.update_xaxes(visible=False, row=1, col=1)
    fig.add_trace(go.Bar(x=data['sum_of_rows'],
                         y=data.index[:-1],
                         orientation='h',
                         showlegend=False,
                         marker=dict(color=data['sum_of_rows'], colorscale=colorscale)),
                  row=2, col=2)
    fig.update_yaxes(visible=False, row=2, col=2)

    fig.add_heatmap(z=data.drop('sum_of_rows', axis='columns').drop('sum_of_cols', axis='index'),
                    x=data.columns[:-1],
                    y=data.index[:-1],
                    hoverongaps=False,
                    showlegend=False,
                    showscale=False,
                    colorscale=colorscale,
                    row=2, col=1)
    fig.show()


def plot_graph(data: DataFrame, min_val: int = 0):
    # https://plotly.com/python/v3/3d-network-graph/
    # https://towardsdatascience.com/python-interactive-network-visualization-using-networkx-plotly-and-dash-e44749161ed7
    # https://plotly.com/python/network-graphs/#create-network-graph
    assert list(data.index) == list(data.columns)
    assert np.allclose(data.values, data.transpose().values, equal_nan=True)
    np.fill_diagonal(data.values, np.nan)

    PERCENTILE_CUTOFF = 0.5
    drop_labels = data[data.sum().rank(method='first', pct=True) <= PERCENTILE_CUTOFF].index
    data.drop(drop_labels, axis=0, inplace=True)
    data.drop(drop_labels, axis=1, inplace=True)

    G = ig.Graph.Adjacency(
        np.where(np.logical_and(np.isfinite(data.values), np.greater(data.values, min_val)), True, False).tolist(),
        mode=ig.ADJ_UNDIRECTED
    )
    # G.es['weight'] = data[data > min_val].values

    SCALE = 100
    # layout = G.layout('sphere', dim=3)
    layout = G.layout_auto(dim=3)
    Xn, Yn, Zn = list(zip(*layout))
    Xn = tuple(map(lambda x: SCALE * x, Xn))
    Yn = tuple(map(lambda x: SCALE * x, Yn))
    Zn = tuple(map(lambda x: SCALE * x, Zn))

    clustering = G.community_fastgreedy().as_clustering()
    G = clustering.graph
    clusters = clustering.membership

    percentiles = data.unstack().rank(method='first', pct=True).values.reshape(data.shape)
    k: int = 10
    Xe = {i: [] for i in range(k)}
    Ye = {i: [] for i in range(k)}
    Ze = {i: [] for i in range(k)}

    def get_width(val):
        min_width, max_width = 0, 5  # in px
        return min_width + (max_width - min_width) * val / (k - 1)
        # if val < k / 2:
        #     return 0
        # else:
        #     val = 2 * (val - k / 2)
        #     return min_width + (max_width - min_width) * val / (k - 1)

    def get_alpha(val):
        min_alpha, max_alpha = 0.01, 0.2
        if val <= k / 2:
            return min_alpha
        else:
            val = (val - 1 - k / 2) / (k / 2 - 2)
            return min_alpha + (max_alpha - min_alpha) * val

    We = {
        i: get_width(i) for i in range(k)
    }
    Ae = {
        i: get_alpha(i) for i in range(k)
    }
    traces = []
    quantiles = []
    for e in G.es:
        s = e.source
        t = e.target
        percentile = percentiles[s][t]
        quantile = min(k - 1, int(k * percentiles[s][t]))

        quantiles.append(quantile)
        xs = [[layout[s][0], layout[t][0], None]]
        ys = [[layout[s][1], layout[t][1], None]]
        zs = [[layout[s][2], layout[t][2], None]]
        w = data.values[s][t]
        Xe[quantile] += [SCALE * layout[s][0], SCALE * layout[t][0], None]
        Ye[quantile] += [SCALE * layout[s][1], SCALE * layout[t][1], None]
        Ze[quantile] += [SCALE * layout[s][2], SCALE * layout[t][2], None]

        # TODO: bin edges by weight (decile?) to have coarse width variation
        # edge_trace = go.Scatter3d(
        #     x=xs, y=ys, z=zs,
        #     mode='lines',
        #     line=dict(
        #         width=w
        #     )
        # )
        # traces.append(edge_trace)

    for i in range(k):
        if We[i] > 0:
            traces.append(go.Scatter3d(
                x=Xe[i], y=Ye[i], z=Ze[i],
                mode='lines',
                line=dict(
                    width=We[i],
                    color=f'rgba(0,0,0,{Ae[i]})'
                )
            ))

    min_size, max_size = 2, 20  # in px
    sizes = data.sum(axis=0)
    sizes /= sizes.max()  # in [0, 1]
    sizes = min_size + (max_size - min_size) * sizes  # in [min_size, max_size]

    node_trace = go.Scatter3d(
        x=Xn, y=Yn, z=Zn,
        mode='markers',
        marker=dict(
            size=sizes,
            # color=data.sum(axis=0),
            color=clusters,
            colorscale='Jet'
        )
    )

    fig = go.Figure(
        data=traces + [node_trace]
    )
    fig.show()


def plot_cooc(df: DataFrame):
    LC_cooc = CoOccurrence()
    for ls, cs in zip(df['languages'], df['countries']):
        LC_cooc.update(ls.split('+'), cs.split('+'))

    LK_cooc = CoOccurrence()
    for ls, k in zip(df['languages'], df['keywords']):
        LK_cooc.update(ls.split('+'), k.split('+'))

    KK_cooc = CoOccurrence()
    for k in df['keywords']:
        KK_cooc.update(k.split('+'), k.split('+'))

    LC = sort(LC_cooc.get_dataframe())
    LK = sort(LK_cooc.get_dataframe())
    KK = sort(KK_cooc.get_dataframe())

    # plot_raw(KK)
    # plot_raw(LC)
    # plot_raw(LK)

    plot_graph(KK)
    # plot_sankey(LC.transpose())
    # plot_marginal(LC)
    # plot_marginal(LK)


def multi_label_binarize(data: DataFrame, columns, prepend_cols=None):
    if prepend_cols is None:
        prepend_cols = []
    mlb = MultiLabelBinarizer()
    features = []
    for i, col in enumerate(columns):
        binarized = mlb.fit_transform(data[col])
        new_columns = mlb.classes_
        if prepend_cols is not None:
            new_columns = [prepend_cols[i] + nc for nc in new_columns]

        features.append(pd.DataFrame(binarized, columns=new_columns, index=data.index))

    return pd.concat(features, axis=1)


if __name__ == '__main__':
    cols = ['date', 'id', 'countries', 'languages', 'keywords']
    dtypes = {c: 'string' for c in cols}
    df = pd.read_csv('../data/posts.csv', usecols=cols, dtype=dtypes)  # .fillna('')

    df['countries_list'] = split(df, 'countries', fill_na='')
    df['languages_list'] = split(df, 'languages', fill_na='')
    df['keywords_list'] = split(df, 'keywords', fill_na='')

    # mlb = MultiLabelBinarizer()  # sparse_output=True)
    # features = pd.DataFrame(mlb.fit_transform(df['countries']), columns=['C: ' + c for c in mlb.classes_],
    #                       index=df.index)
    features = multi_label_binarize(df, ['countries_list', 'languages_list', 'keywords_list'], ['C ', 'L ', 'K '])

    # manifold = Isomap(n_components=3, n_jobs=-1)
    manifold = SpectralEmbedding(n_components=3, n_jobs=-1)
    # manifold = MDS(n_components=3, n_jobs=-1)
    # manifold = PCA(n_components=3)
    # manifold = TSNE(n_components=3, n_jobs=-1)
    # manifold=LocallyLinearEmbedding(n_components=3, n_jobs=-1, method='ltsa')
    embedded = manifold.fit_transform(features)

    targets = pd.Categorical(
        df['languages'],
        ordered=True,
        categories=df['languages'].value_counts(ascending=True).index
    ).codes

    layout = go.Layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False)
        )
    )

    scatter = go.Scatter3d(
        x=embedded[:, 0], y=embedded[:, 1], z=embedded[:, 2],
        customdata=df['languages_list'],
        hovertemplate="%{customdata}",
        mode='markers+text',
        marker=dict(
            color=targets,
            colorscale='Jet',
            size=2
        )
    )

    fig = go.Figure(data=scatter, layout=layout)
    fig.show()

    # df['lang_iso'] = df['languages'].apply(lambda ls: [language_to_iso2(l) for l in ls.split('+')])
    # df['cc'] = df['countries'].apply(lambda cs: [territory_to_iso3(c) for c in cs.split('+')])
    # df['territories'] = df['languages'].apply(territories_from_language)
    # df = explode_replace(df, 'territories', 'territory')
    # # df.language = df.language.apply(lang2iso)
    # # df['iso3'] = df.countries.apply(to_iso3)
    # fig = px.choropleth(df[::-1],
    #                     locations='territory',
    #                     hover_name='territory',
    #                     scope='europe',
    #                     animation_frame='id',
    #                     animation_group='date')
    # # fig = px.bar(df[::-1], x='territory', y=[1 for _ in range(len(df))], animation_frame='date')
    # fig.show()
