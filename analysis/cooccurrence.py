from collections import defaultdict
from typing import Dict, Sequence

import pandas as pd


class CoOccurrence:
    M: Dict[str, Dict[str, int]]

    def __init__(self):
        self.M = defaultdict(lambda: defaultdict(int))

    def update(self, row_entities: Sequence[str], column_entries: Sequence[str]):
        for r in row_entities:
            for c in column_entries:
                self.M[r][c] += 1

    def get_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame.from_dict(self.M)
