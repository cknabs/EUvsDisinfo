import logging

import plotly.graph_objects as go
from pandas import DataFrame

LOGGER = logging.getLogger(__name__)


def explode_replace(data: DataFrame, old_name: str, new_name: str):
    data[old_name] = data[old_name].str.split('+')
    data = data.explode(old_name)
    data = data.rename(columns={old_name: new_name})
    return data


def split(data: DataFrame, column: str, fill_na=None):
    res = data[column].str.split('+')
    if fill_na is not None:
        res.fillna(fill_na, inplace=True)
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
