from collections import defaultdict
from typing import Dict, Sequence

import pandas as pd


class CoOccurrence:
    M: Dict[str, Dict[str, int]]

    def __init__(self):
        self.M = defaultdict(lambda: defaultdict(int))

    def update(self, rows: Sequence[str], cols: Sequence[str]):
        for r in rows:
            for c in cols:
                self.M[r][c] += 1

    def get_dataframe(self) -> pd.DataFrame:
        # TODO: return a sparse object (don't store NA values explicitly)
        # TODO: switch from float64 to pandas' Int64?
        return pd.DataFrame.from_dict(self.M)
