import pandas as pd

from apps.util import explode_replace

# Data
cols = ['date', 'countries', 'languages', 'keywords']
dtypes = {c: 'string' for c in cols}
df = pd.read_csv('data/posts.csv', usecols=cols, dtype=dtypes).fillna('')

date_language = df[['date', 'languages']]
date_language = explode_replace(date_language, 'languages', 'language')
date_language = pd.pivot_table(date_language, index=['date'], columns=['language'], aggfunc=lambda x: len(x))
date_language.rename(columns={'': 'Other'}, inplace=True)
date_language.index.rename('date', inplace=True)
date_language.fillna(0, inplace=True)
