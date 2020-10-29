from urllib.parse import urlparse

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

from analysis.cooccurrence import CoOccurrence
from viz.util import fig_graph, sort

if __name__ == '__main__':
    cols = ['url', 'title', 'date', 'language', 'authors', 'twitter', 'facebook', 'id']
    dtypes = {c: 'string' for c in cols}
    df = pd.read_csv('../data/out.csv', usecols=cols, dtype=dtypes).fillna('')

    df['domain'] = df['url'].apply(lambda url: urlparse(url).netloc)

    cooc_social = CoOccurrence()
    cooc_content = CoOccurrence()
    cooc_topic = CoOccurrence()
    for _, group in df.groupby('id'):
        for entries in zip(group['twitter'], group['facebook'], group['domain']):
            entries = [e for e in entries if len(e) > 0]  # Omit empty entries (NA in original data)
            cooc_social.update(entries, entries)
        cooc_topic.update(group['domain'], group['domain'])
        for _, title_group in group.groupby('title'):
            # TODO: how to group subdomains (e.g., arabic.rt.com vs. rt.com)?
            cooc_content.update(title_group['domain'], title_group['domain'])

    res_social = sort(cooc_social.get_dataframe())
    res_content = sort(cooc_content.get_dataframe())
    # res_topic = sort(cooc_topic.get_dataframe())

    fig_social = fig_graph(res_social, 'Publishers and Social Media Profiles', percentile_cutoff=0.9)
    fig_content = fig_graph(res_content, 'Publishers', percentile_cutoff=0.9)

    app = dash.Dash(__name__)
    app.layout = html.Div(children=[
        html.H1(children='Exploring the EUvsDisinfo database'),
        html.Div(
            dcc.Graph(id='social', figure=fig_social),
            style=dict(width='50%', display='inline-block'),
        ),
        html.Div(
            dcc.Graph(id='publishers', figure=fig_content),
            style=dict(width='50%', display='inline-block')
        )
    ])

    app.run_server(debug=True)
