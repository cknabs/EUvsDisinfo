import json
from typing import Dict, List

import country_converter as coco
import langcodes
import pandas as pd
import plotly.express as px
from pandas import DataFrame

LANGUAGE2TERRITORIES: Dict[str, List[str]]
with open('../language-territories.json') as l2t:
    LANGUAGE2TERRITORIES = json.load(l2t)


def to_iso3(name: str) -> str:
    if name == 'UK':
        return 'GBR'
    else:
        return coco.convert(name, to='ISO3')


def lang2iso(lang: str) -> str:
    return langcodes.find(lang).language


def lang2territories(lang: str) -> List[str]:
    lang_iso = langcodes.find(lang).language
    iso2 = LANGUAGE2TERRITORIES[lang_iso]
    iso3 = coco.convert(iso2, src='ISO2', to='ISO3')
    return iso3


def explode_replace(df: DataFrame, old_name: str, new_name: str):
    # df[old_name] = df[old_name].str.split('+')
    df = df.explode(old_name)
    df = df.rename(columns={old_name: new_name})
    return df


df = pd.read_csv('../posts.csv', usecols=['date', 'countries', 'languages'])  # TODO: regenerate data/*.csv
df['territories'] = df['languages'].apply(lang2territories)
df = explode_replace(df, 'territories', 'territory')
# df.language = df.language.apply(lang2iso)
# df['iso3'] = df.countries.apply(to_iso3)

fig = px.choropleth(df[::-1],
                    locations='territory',
                    hover_name='territory',
                    scope='europe',
                    animation_frame='date')
# fig = px.bar(df[::-1], x='territory', y=[1 for _ in range(len(df))], animation_frame='date')
fig.show()
