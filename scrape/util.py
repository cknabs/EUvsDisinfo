import argparse
from typing import List

LIST_SEPARATOR: str = "+"


def list2str(lst: List[str]) -> str:
    assert all(LIST_SEPARATOR not in elem for elem in lst)
    return LIST_SEPARATOR.join(lst)


def str2list(string: str) -> List[str]:
    return string.split(LIST_SEPARATOR)


def check_non_negative(string: str) -> int:
    value = int(string)
    if value < 0:
        raise argparse.ArgumentTypeError(
            f"argument must be positive (was {value})"
        )
    return value
