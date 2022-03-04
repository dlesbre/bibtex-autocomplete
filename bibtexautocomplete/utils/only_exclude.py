"""
A class designed to represent a container defined by either
a list of contained elements or a list of excluded elements
"""


from typing import Callable, Container, Iterable, Optional, Sized, TypeVar

T = TypeVar("T")
Q = TypeVar("Q")


class SizedContainer(Sized, Container[T]):
    """Type hint for containers that define __len__"""

    pass


class OnlyExclude(Container[T]):
    """Class to represent a set defined by either
    - only containing elements
    - not containing elements
    Implement the in operator
    and a filter iterator"""

    onlys: Optional[Container[T]]
    nots: Optional[Container[T]]

    def __init__(
        self, onlys=Optional[Container[T]], nots=Optional[Container[T]]
    ) -> None:
        """Create a new instance with onlys or nots.
        If both are specified, onlys takes precedence.
        Not that an empty container is not None,
        so an empty onlys will create a container containing nothing"""

        self.onlys = onlys
        self.nots = nots

    @classmethod
    def from_nonempty(
        cls, onlys: SizedContainer[T], nots: SizedContainer[T]
    ) -> "OnlyExclude[T]":
        """A different initializer, which considers empty containers to be None"""
        o = onlys if len(onlys) > 0 else None
        n = nots if len(nots) > 0 else None
        return cls(o, n)  # We need the class for type instanciation

    def __contains__(self, obj: T) -> bool:  # type: ignore[override]
        """Check if obj is valid given the exclusion rules"""
        if self.onlys is not None:
            return obj in self.onlys
        if self.nots is not None:
            return obj not in self.nots
        return True

    def filter(self, iterable: Iterable[Q], map: Callable[[Q], T]) -> Iterable[Q]:
        """Returns a filtered Iterator
        Note that this filter is consumed after the first use"""
        return filter(lambda x: map(x) in self, iterable)
