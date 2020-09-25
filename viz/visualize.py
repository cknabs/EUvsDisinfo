import pandas as pd
import plotly.graph_objects as go
from pandas import DataFrame
from plotly.subplots import make_subplots

from analysis.cooccurrence import CoOccurrence


def explode_replace(df: DataFrame, old_name: str, new_name: str):
    # df[old_name] = df[old_name].str.split('+')
    df = df.explode(old_name)
    df = df.rename(columns={old_name: new_name})
    return df


def sort_by_sum(df: DataFrame) -> DataFrame:
    sum_of_rows = df.sum(axis='columns')
    sum_of_cols = df.sum(axis='index')
    df['sum_of_rows'] = sum_of_rows
    df.loc['sum_of_cols'] = sum_of_cols
    return df \
        .sort_values(by='sum_of_rows', ascending=False, axis='index') \
        .drop('sum_of_rows', axis='columns') \
        .sort_values(by='sum_of_cols', ascending=False, axis='columns') \
        .drop('sum_of_cols', axis='index')


def plot_marginal(df: DataFrame):
    sum_of_rows = df.sum(axis='columns')
    sum_of_cols = df.sum(axis='index')
    df['sum_of_rows'] = sum_of_rows
    df.loc['sum_of_cols'] = sum_of_cols
    df = df.sort_values(by='sum_of_rows', ascending=False, axis='index') \
        .sort_values(by='sum_of_cols', ascending=False, axis='columns')
    fig = make_subplots(rows=2, cols=2,
                        row_heights=[0.2, 0.8], column_width=[0.8, 0.2],
                        vertical_spacing=0.01, horizontal_spacing=0.01
                        )
    fig.update_layout(template='plotly_dark')

    colorscale = 'solar'

    fig.add_trace(go.Bar(y=df.transpose()['sum_of_cols'],
                         x=df.columns[:-1],
                         showlegend=False,
                         marker=dict(color=df.transpose()['sum_of_cols'], colorscale=colorscale)),
                  row=1, col=1)
    fig.update_xaxes(visible=False, row=1, col=1)
    fig.add_trace(go.Bar(x=df['sum_of_rows'],
                         y=df.index[:-1],
                         orientation='h',
                         showlegend=False,
                         marker=dict(color=df['sum_of_rows'], colorscale=colorscale)),
                  row=2, col=2)
    fig.update_yaxes(visible=False, row=2, col=2)

    fig.add_heatmap(z=df.drop('sum_of_rows', axis='columns').drop('sum_of_cols', axis='index'),
                    x=df.columns[:-1],
                    y=df.index[:-1],
                    hoverongaps=False,
                    showlegend=False,
                    showscale=False,
                    colorscale=colorscale,
                    row=2, col=1)
    fig.show()


df = pd.read_csv('../posts.csv',
                 usecols=['date', 'id', 'countries', 'languages', 'keywords'])  # TODO: regenerate data/*.csv

LC_cooc = CoOccurrence()
for ls, cs in zip(df['languages'], df['countries']):
    LC_cooc.update(ls.split('+'), cs.split('+'))

LK_cooc = CoOccurrence()
for ls, k in zip(df['languages'], df['keywords']):
    LK_cooc.update(ls.split('+'), k.split('+'))

LC = sort_by_sum(LC_cooc.get_dataframe())
LK = sort_by_sum(LK_cooc.get_dataframe())

plot_marginal(LC)
plot_marginal(LK)

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
