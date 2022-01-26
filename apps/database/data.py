from datetime import datetime

import pandas as pd

from apps.util import explode_replace

# Data
cols = ["id", "title", "date", "languages", "countries"]
dtypes = {c: "string" for c in cols}
df = pd.read_csv("data/posts.csv", usecols=cols, dtype=dtypes).fillna("")
df["date"] = pd.to_datetime(df["date"])
df = explode_replace(df, "languages", "language")
df = explode_replace(df, "countries", "country")

# Number of entries per language per date
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


# Number of entries per countries per month
def to_month(x):
    return datetime.strftime(x, "%Y-%m")


counts_by_date = (
    df[["date", "country"]]
    .reset_index(drop=True)
    .value_counts()
    .reset_index()
    .rename(columns={0: "count"})
)
counts_by_date["month"] = counts_by_date["date"].map(to_month)
counts_by_date = counts_by_date.drop(columns=["date"]).sort_values(by="month")

all_months = (
    pd.date_range(
        counts_by_date["month"].min(),
        counts_by_date["month"].max(),
        freq="M",
    )
    .map(to_month)
    .to_frame(index=False, name="month")
)
all_countries = pd.Series(
    counts_by_date["country"].unique(), name="country"
).to_frame()
fill_vals = pd.merge(all_months, all_countries, how="cross")
fill_vals["count"] = 0

counts_by_date = (
    pd.concat([counts_by_date, fill_vals])
    .drop_duplicates(keep="first")
    .sort_values(by="month")
)
