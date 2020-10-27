from typing import List

LIST_SEPARATOR: str = '+'


def list2str(lst: List[str]) -> str:
    assert all(LIST_SEPARATOR not in elem for elem in lst)
    return LIST_SEPARATOR.join(lst)


def str2list(string: str) -> List[str]:
    return string.split(LIST_SEPARATOR)
