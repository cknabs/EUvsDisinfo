from urllib.parse import urlparse

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output

from analysis.cooccurrence import CoOccurrence
from viz.util import fig_graph, sort

cols = ['url', 'title', 'date', 'language', 'authors', 'twitter', 'facebook', 'id']
dtypes = {c: 'string' for c in cols}
df = pd.read_csv('../data/out.csv', usecols=cols, dtype=dtypes).fillna('')[:5000]

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

app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])


@app.callback(
    [Output('fig-social', 'figure'),
     Output('fig-publishers', 'figure')],
    [Input('percentile-slider', 'value')]
)
def update_figures(value):
    percentile_cutoff = 1.0 - value
    fig_social = fig_graph(res_social, 'Publishers and Social Media Profiles', percentile_cutoff=percentile_cutoff)
    fig_publishers = fig_graph(res_content, 'Publishers', percentile_cutoff=percentile_cutoff)
    return fig_social, fig_publishers


@app.callback(
    Output('percentile-value', 'children'),
    [Input('percentile-slider', 'value')]
)
def update_output(value):
    percentile_value = f"Show top {int(100 * value)}% only)"
    return percentile_value


if __name__ == '__main__':
    # res_topic = sort(cooc_topic.get_dataframe())

    fig_social = fig_graph(res_social, 'Publishers and Social Media Profiles', percentile_cutoff=0.9)
    fig_content = fig_graph(res_content, 'Publishers', percentile_cutoff=0.9)

    app.layout = html.Div(children=[
        html.H1(children='Exploring the EUvsDisinfo database'),
        html.Div(style=dict(width='20%', display='inline-block'),
                 children=[
                     html.Div(id='percentile-value'),
                     dcc.Slider(id='percentile-slider',
                                min=0.01,
                                max=1,
                                step=0.01,
                                value=0.1,
                                marks={i / 100: f"{i}%" for i in range(0, 100, 10)})
                 ]),
        html.Div(style=dict(width='40%', display='inline-block'),
                 children=[
                     dcc.Graph(id='fig-social'),  # , figure=fig_social),
                 ]),
        html.Div(
            dcc.Graph(id='fig-publishers', figure=fig_content),
            style=dict(width='40%', display='inline-block')
        )
    ])

    app.run_server(debug=True)
