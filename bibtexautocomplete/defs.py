# Constants, usefull functions...
import logging
from re import search
from typing import Callable, Container, Dict, Iterable, Optional, Sized, TypeVar

# =====================================================
# Constants
# =====================================================

NAME = "bibtexautocomplete"
VERSION = "0.1"
URL = "https://github.com/dlesbre/bibtex-autocomplete"
LICENSE = "MIT"

EMAIL = "dorian.lesbre" + chr(64) + "gmail.com"

CONNECTION_TIMEOUT = 10.0  # seconds

USER_AGENT = f"{NAME}/{VERSION} ({URL}; mailto:{EMAIL})"

DOI_REGEX = r"(10\.\d{4,5}\/[\S]+[^;,.\s])$"

EntryType = Dict[str, str]  # Type of a bibtex entry
ResultType = Dict[str, Optional[str]]  # Type of query results

# =====================================================
# Logger
# =====================================================

# create logger
logger = logging.getLogger(NAME)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

# =====================================================
# Utility functions
# =====================================================


def str_normalize(string: str) -> str:
    """Normalize string for decent comparison"""
    res = ""
    prev_space = False
    for x in string:
        if x.isalnum():
            res += x
            prev_space = False
        elif not prev_space:
            res += " "
            prev_space = True
    return res.lower().strip()


def str_similar(s1: str, s2: str) -> bool:
    """String equality, case insensitive"""
    return str_normalize(s1) == str_normalize(s2)


def extract_doi(doi_or_url: Optional[str]) -> Optional[str]:
    """Returns doi to canonical form (i.e. removing url)"""
    if doi_or_url is not None:
        match = search(DOI_REGEX, doi_or_url)
        if match is not None:
            return match.group(1)
    return None


# =====================================================
# Utility functions
# =====================================================

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
        return filter(lambda x: map(x) in self, iterable)
