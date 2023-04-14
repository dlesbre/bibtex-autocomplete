from typing import Callable, Iterable, List, Set, Tuple, TypeVar

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


def list_sort_using(
    to_sort: Iterable[Q], reference: List[T], map: Callable[[Q], T]
) -> List[Q]:
    """Sorts to_sort based on the order in reference, using map for conversion"""
    order = {q: i for i, q in enumerate(reference)}
    return sorted(to_sort, key=lambda t: order[map(t)])
