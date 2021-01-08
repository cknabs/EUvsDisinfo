from urllib.parse import urlparse

import pandas as pd

from analysis.cooccurrence import CoOccurrence
from apps.util import sort

cols = [
    "url",
    "title",
    "date",
    "language",
    "authors",
    "twitter",
    "facebook",
    "id",
]
dtypes = {c: "string" for c in cols}
df = pd.read_csv("data/out.csv", usecols=cols, dtype=dtypes).fillna("")[:5000]

df["domain"] = df["url"].apply(lambda url: urlparse(url).netloc)

cooc_social = CoOccurrence()
cooc_content = CoOccurrence()
cooc_topic = CoOccurrence()
# TODO: add tqdm
for _, group in df.groupby("id"):
    for entries in zip(group["twitter"], group["facebook"], group["domain"]):
        entries = [
            e for e in entries if len(e) > 0
        ]  # Omit empty entries (NA in original data)
        cooc_social.update(entries, entries)
    cooc_topic.update(group["domain"], group["domain"])
    for _, title_group in group.groupby("title"):
        # TODO: how to group subdomains (e.g., arabic.rt.com vs. rt.com)?
        cooc_content.update(title_group["domain"], title_group["domain"])

res_social = sort(cooc_social.get_dataframe())
res_content = sort(cooc_content.get_dataframe())
