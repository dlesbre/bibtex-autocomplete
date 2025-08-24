from typing import Callable, Iterable, List, Optional, Set, Tuple, TypeVar, Union

from bibtexparser.bibdatabase import UndefinedString

T = TypeVar("T")
Q = TypeVar("Q")


def list_unduplicate(lst: List[T]) -> Tuple[List[T], Set[T]]:
    """Unduplicates a list, preserving order
    Returns of set of duplicated elements"""
    unique = list()
    dups = set()
    for x in lst:
        if x in unique:
            dups.add(x)
        else:
            unique.append(x)
    return unique, dups


def list_sort_using(to_sort: Iterable[Q], reference: List[T], map: Callable[[Q], T]) -> List[Q]:
    """Sorts to_sort based on the order in reference, using map for conversion"""
    order = {q: i for i, q in enumerate(reference)}
    return sorted(to_sort, key=lambda t: order[map(t)])


def split_iso_date(date: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract year and month from a YYYY-MM-DD or YYYY-MM date string"""
    year = None
    month = None
    if len(date) >= 4 and date[:4].isnumeric() and 1000 <= int(date[:4]) <= 3000:
        year = date[:4]
        if len(date) >= 7 and date[5:7].isnumeric() and 1 <= int(date[5:7]) <= 12:
            month = date[5:7]
    return year, month


class BTAC_CLI_Error(ValueError):
    """Exception raised for invalid btac command line options/API use"""


class BTAC_File_Error(Exception):
    """Exception raised for invalid file access OR invalid file format"""

    message: str
    previous_error: Union[UndefinedString, IOError, UnicodeDecodeError]

    def __init__(self, message: str, previous_error: Union[UndefinedString, IOError, UnicodeDecodeError]):
        super().__init__()
        self.message = message
        self.previous_error = previous_error
