import pandas as pd
import plotly.graph_objects as go
from pandas import DataFrame
from plotly.subplots import make_subplots
import numpy as np
import networkx as nx
import igraph as ig

from analysis.cooccurrence import CoOccurrence


def explode_replace(data: DataFrame, old_name: str, new_name: str):
    # data[old_name] = data[old_name].str.split('+')
    data = data.explode(old_name)
    data = data.rename(columns={old_name: new_name})
    return data


def sort(data: DataFrame) -> DataFrame:
    """
    Sort the rows and columns of :param data: by the sum of the row/column, using the row/column name to break ties.
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


def plot_graph(data: DataFrame, min_val: int = 0):
    # https://plotly.com/python/v3/3d-network-graph/
    # https://towardsdatascience.com/python-interactive-network-visualization-using-networkx-plotly-and-dash-e44749161ed7
    # https://plotly.com/python/network-graphs/#create-network-graph
    data = data.fillna(0)
    assert list(data.index) == list(data.columns)
    assert np.allclose(data.values, data.transpose().values, equal_nan=True)
    G = ig.Graph.Adjacency((data.values > min_val).tolist())
    G.es['weight'] = data[data > min_val].values
    layout = G.layout('sphere', dim=3)
    Xn, Yn, Zn = list(zip(*layout))
    Xe = []
    Ye = []
    Ze = []
    We = []
    traces = []
    for e in G.es:
        s = e.source
        t = e.target
        xs =[[layout[s][0], layout[t][0], None]]
        ys = [[layout[s][1], layout[t][1], None]]
        zs = [[layout[s][2], layout[t][2], None]]
        w = data.values[s][t]
        Xe += [layout[s][0], layout[t][0], None]
        Ye += [layout[s][1], layout[t][1], None]
        Ze += [layout[s][2], layout[t][2], None]

        # TODO: bin edges by weight (decile?) to have coarse width variation
        # edge_trace = go.Scatter3d(
        #     x=xs, y=ys, z=zs,
        #     mode='lines',
        #     line=dict(
        #         width=w
        #     )
        # )
        # traces.append(edge_trace)

    traces.append(go.Scatter3d(
        x=Xe, y=Ye, z=Ze,
        mode='lines'
    ))

    min_size, max_size = 2, 20  # in px
    widths = data.sum(axis=0)
    widths /= widths.max()  # in [0, 1]
    widths = min_size + (max_size - min_size) * widths  # in [min_size, max_size]

    node_trace = go.Scatter3d(
        x=Xn, y=Yn, z=Zn,
        mode='markers',
        marker=dict(
            size=widths
        )
    )

    fig = go.Figure(data=traces + [node_trace])
    fig.show()


if __name__ == '__main__':
    cols = ['date', 'id', 'countries', 'languages', 'keywords']
    dtypes = {c: 'string' for c in cols}
    df = pd.read_csv('../data/posts.csv', usecols=cols, dtype=dtypes).fillna('')

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

    plot_graph(KK)
    # plot_sankey(LC.transpose())
    # plot_marginal(LC)
    # plot_marginal(LK)

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
