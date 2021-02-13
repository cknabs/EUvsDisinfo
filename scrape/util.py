import argparse
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR = Path(__file__).absolute().parent.parent / "data"
POSTS_FILENAME = "posts.csv"
PUBLICATIONS_FILENAME = "publications.csv"
ANNOTATIONS_FILENAME = "annotations.csv"
SCHEMA_FILENAME = "datapackage.json"

LIST_SEPARATOR: str = "+"


def list2str(lst: List[str]) -> str:
    assert all(LIST_SEPARATOR not in elem for elem in lst)
    return LIST_SEPARATOR.join(lst)


def str2list(string: str) -> List[str]:
    return string.split(LIST_SEPARATOR)


def to_string(val: Any) -> str:
    if val is None:
        return ""
    elif isinstance(val, str):
        return val
    elif isinstance(val, list):
        return list2str(val)
    else:
        return str(val)


def stringify(dictionary: dict) -> Dict[str, str]:
    return {k: to_string(v) for k, v in dictionary.items()}


def check_non_negative(string: str) -> int:
    value = int(string)
    if value < 0:
        raise argparse.ArgumentTypeError(
            f"argument must be positive (was {value})"
        )
    return value
