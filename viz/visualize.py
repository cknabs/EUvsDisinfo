import pandas as pd
import plotly.express as px
from pandas import DataFrame

from analysis.convert import territories_from_language


def explode_replace(df: DataFrame, old_name: str, new_name: str):
    # df[old_name] = df[old_name].str.split('+')
    df = df.explode(old_name)
    df = df.rename(columns={old_name: new_name})
    return df


df = pd.read_csv('../posts.csv', usecols=['date', 'id', 'countries', 'languages'])  # TODO: regenerate data/*.csv
df['territories'] = df['languages'].apply(territories_from_language)
df = explode_replace(df, 'territories', 'territory')
# df.language = df.language.apply(lang2iso)
# df['iso3'] = df.countries.apply(to_iso3)

fig = px.choropleth(df[::-1],
                    locations='territory',
                    hover_name='territory',
                    scope='europe',
                    animation_frame='id',
                    animation_group='date')
# fig = px.bar(df[::-1], x='territory', y=[1 for _ in range(len(df))], animation_frame='date')
fig.show()
