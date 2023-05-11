"""
A class designed to represent a container defined by either
a list of contained elements or a list of excluded elements
"""


from typing import Callable, Container, Iterable, List, Optional, Set, Tuple, TypeVar

U = TypeVar("U", covariant=True)


T = TypeVar("T")
Q = TypeVar("Q")


class OnlyExclude(Container[T]):
    """Class to represent a set defined by either
    - only containing elements
    - not containing elements
    Implement the in operator
    and a filter iterator"""

    onlys: Optional[List[T]]
    nots: Optional[List[T]]
    default: bool = True

    def __init__(self, onlys: Optional[List[T]], nots: Optional[List[T]]) -> None:
        """Create a new instance with onlys or nots.
        If both are specified, onlys takes precedence.
        Not that an empty container is not None,
        so an empty onlys will create a container containing nothing"""

        self.onlys = onlys
        self.nots = nots

    @classmethod
    def from_nonempty(cls, onlys: List[T], nots: List[T]) -> "OnlyExclude[T]":
        """A different initializer, which considers empty containers to be None"""
        o = onlys if len(onlys) > 0 else None
        n = nots if len(nots) > 0 else None
        return cls(o, n)  # We need the class for type instanciation

    def __contains__(self, obj: T) -> bool:  # type: ignore[override]
        """Check if obj is valid given the exclusion rules
        returns self.default if neither onlys nor nots is set"""
        if self.onlys is not None:
            return obj in self.onlys
        if self.nots is not None:
            return obj not in self.nots
        return self.default

    def filter(self, iterable: Iterable[Q], map: Callable[[Q], T]) -> Iterable[Q]:
        """Returns a filtered Iterator
        Note that this filter is consumed after the first use"""
        return filter(lambda x: map(x) in self, iterable)

    def unused(self, iterable: Iterable[T]) -> Tuple[Set[T], Set[T]]:
        """Return set of unused filters:
        - set of unused only filters
        - set of unused not filters"""
        if self.onlys is not None:
            unused = set(self.onlys)
            for x in iterable:
                if x in self.onlys:
                    unused.discard(x)
            nots = set() if self.nots is None else set(self.nots)
            return unused, nots
        if self.nots is not None:
            unused = set(self.nots)
            for x in iterable:
                if x in self.nots:
                    unused.discard(x)
            return set(), unused
        return set(), set()
