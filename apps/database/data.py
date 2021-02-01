import pandas as pd

from apps.util import explode_replace

# Data
cols = ["id", "title", "date", "languages"]
dtypes = {c: "string" for c in cols}
df = pd.read_csv("data/posts.csv", usecols=cols, dtype=dtypes).fillna("")
df["date"] = pd.to_datetime(df["date"])
df = explode_replace(df, "languages", "language")

date_language = df[["date", "language"]]
date_language = pd.pivot_table(
    date_language,
    index=["date"],
    columns=["language"],
    aggfunc=lambda x: len(x),
)
date_language.rename(columns={"": "Other"}, inplace=True)
date_language.index.rename("date", inplace=True)
date_language.fillna(0, inplace=True)

df.index = df["date"]
