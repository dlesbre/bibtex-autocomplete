# Constants, usefull functions...
import logging
from json import JSONDecodeError, JSONDecoder
from re import search
from sys import stderr, stdout
from typing import (
    Any,
    Callable,
    Container,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sized,
    Tuple,
    TypeVar,
    Union,
)

# =====================================================
# Constants
# =====================================================

NAME = "bibtexautocomplete"
VERSION = "0.2"
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


class LevelFilter(logging.Filter):
    def __init__(self, low, high):
        self._low = low
        self._high = high
        logging.Filter.__init__(self)

    def filter(self, record):
        if self._low <= record.levelno <= self._high:
            return True
        return False


# custom level
PROGRESS = logging.INFO + 2
logging.addLevelName(PROGRESS, "INFO")

DEFAULT_LEVEL = PROGRESS

# create logger
logger = logging.getLogger(NAME)
error_handler = logging.StreamHandler(stderr)
error_handler.addFilter(LevelFilter(logging.WARN, logging.CRITICAL))
error_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
logger.addHandler(error_handler)
info_handler = logging.StreamHandler(stdout)
info_handler.addFilter(LevelFilter(0, logging.WARN - 1))
logger.addHandler(info_handler)


def set_logger_level(level: int) -> None:
    """Translate my program levels into logger levels
    -1 = silent => logging.ERROR
    0 = default => PROGRESS
    1 = verbose => logging.INFO
    2 = very verbose => logging.DEBUG"""
    if level < 0:
        formatter_str = "%(message)s"
        logger.setLevel(logging.ERROR)
    elif level == 0:
        formatter_str = "%(message)s"
        logger.setLevel(PROGRESS)
    elif level == 1:
        formatter_str = "%(asctime)s - %(message)s"
        logger.setLevel(logging.INFO)
    else:
        formatter_str = "%(asctime)s - %(levelname)s - %(message)s"
        logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        formatter_str,
        datefmt="%H:%M:%S",
    )
    info_handler.setFormatter(formatter)


set_logger_level(0)

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
        """Returns a filtered Iterator
        Note that this filter is consumed after the first use"""
        return filter(lambda x: map(x) in self, iterable)


JSONType = Union[Dict[str, Any], List[Any], int, float, str, bool, None]

S = TypeVar("S", bound=JSONType)


class SafeJSON:
    """class designed to make failess accesses to a JSON-like structure
    (recursive structure of either Dict[str, SafeJSON], List[SafeJSON], int, float, str, bool, None)

    defines get_item to seamlessly access dict entries (if item is str) or list element (if item is int)
    """

    value: JSONType

    def __init__(self, value: JSONType) -> None:
        self.value = value

    def __getitem__(self, key: Union[int, str]) -> "SafeJSON":
        result: JSONType = None
        if isinstance(key, int):
            if key >= 0 and isinstance(self.value, list) and len(self.value) > key:
                result = self.value[key]
        else:
            if isinstance(self.value, dict):
                result = self.value.get(key)
        return SafeJSON(result)

    @staticmethod
    def from_str(json: str) -> "SafeJSON":
        """Parses a json string into SafeJSON, returns SafeJSON(None) if invalid string"""
        try:
            decoded = JSONDecoder().decode(json)
        except JSONDecodeError:
            return SafeJSON(None)  # empty
        return SafeJSON(decoded)

    @staticmethod
    def from_bytes(json: bytes) -> "SafeJSON":
        """Parses a json bytes string into SafeJSON, returns SafeJSON(None) if invalid string"""
        return SafeJSON.from_str(json.decode())

    def dict_contains(self, key: str) -> bool:
        """Returns true if self is a dict and has the given key"""
        if isinstance(self.value, dict):
            return key in self.value
        return False

    def to_str(self) -> Optional[str]:
        """Returns the value if it is an str, None otherwise"""
        if isinstance(self.value, str):
            return self.value
        return None

    def force_str(self) -> Optional[str]:
        """Returns str(value) if valus is str, int, float or bool"""
        if isinstance(self.value, (str, int, bool, float)):
            return str(self.value)
        return None

    def to_int(self) -> Optional[int]:
        """Returns the value if it is an int, None otherwise"""
        if isinstance(self.value, int):
            return self.value
        return None

    def to_float(self) -> Optional[float]:
        """Returns the value if it is a float, None otherwise"""
        if isinstance(self.value, float):
            return self.value
        return None

    def to_bool(self) -> Optional[bool]:
        """Returns the value if it is a bool, None otherwise"""
        if isinstance(self.value, bool):
            return self.value
        return None

    def to_list(self) -> Optional[List[Any]]:
        """Returns the value if it is an list, None otherwise"""
        if isinstance(self.value, list):
            return self.value
        return None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        """Returns the value if it is a dict, None otherwise"""
        if isinstance(self.value, dict):
            return self.value
        return None

    def iter_list(self) -> "Iterator[SafeJSON]":
        """Iterate through self if it is a list
        else yields nothing"""
        if isinstance(self.value, list):
            for x in self.value:
                yield SafeJSON(x)

    def iter_dict(self) -> "Iterator[Tuple[str, SafeJSON]]":
        """Iterate through self if it is a list
        else yields nothing"""
        if isinstance(self.value, dict):
            for key, val in self.value.items():
                yield key, SafeJSON(val)
