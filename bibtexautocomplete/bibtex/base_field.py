from abc import abstractmethod
from functools import cmp_to_key
from re import split
from typing import (
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
)

from ..utils.logger import logger


class Comparable(Protocol):
    """Protocol for annotating comparable types."""

    @abstractmethod
    def __lt__(self: "T", other: "T") -> bool:
        pass


T = TypeVar("T", bound=Comparable)
COORD = Tuple[Optional[int], Optional[int]]
COORD_T = Tuple[COORD, T]


FIELD_FULL_MATCH = 100
FIELD_NO_MATCH = 0
SOURCE_SEPARATOR = ", "


class BibtexField(Generic[T]):
    """A bibtex field, represented by type T
    for most T = str, but there are some exceptions:
    - authors: T = List[Author]
    - year, month, issn, isbn: T = int
    """

    counter: int = 0

    id: int
    source: str
    value: Optional[T]

    def __init__(self, source: str) -> None:
        self.value = None
        self.source = source
        self.id = BibtexField.counter
        BibtexField.counter += 1

    #  Methods to override in subclasses

    @classmethod
    def normalize(cls, value: T) -> Optional[T]:
        """Return a normal representation of the entry
        Can return None if invalid format"""
        return value

    @classmethod
    def slow_check(cls, value: T) -> bool:
        """Performs a slow check (e.g. query URL to ensure it resolves)
        Only done if we want to use this in our field"""
        return True

    @classmethod
    def match_values(cls, a: T, b: T) -> int:
        """returns a match score: 0 <= score <= FIELD_FULL_MATCH"""
        if a == b:
            return FIELD_FULL_MATCH
        return FIELD_NO_MATCH

    @classmethod
    def combine_values(cls, a: T, b: T) -> T:
        """When two values match, choose which one to keep"""
        return a

    @classmethod
    def to_bibtex(cls, value: T) -> str:
        """Return the non-None value as a Bibtex string"""
        return str(value)

    @classmethod
    def convert(cls, value: str) -> Optional[T]:
        raise NotImplementedError("override in child classes")

    #  Common methods

    def slow_check_none(self) -> bool:
        """Performs a slow check (e.g. query URL to ensure it resolves)
        Only done if we want to use this in our field"""
        if self.value is None:
            return False
        return self.slow_check(self.value)

    def matches(self, other: "BibtexField[T]") -> Optional[int]:
        """returns a match score: 0 <= score <= FIELD_FULL_MATCH
        Returns None if one of the values is None"""
        if self.value is None or other.value is None:
            return None
        return self.match_values(self.value, other.value)

    def combine(self, other: "BibtexField[T]") -> "BibtexField[T]":
        """Merges both fields to return the one with maximum information
        (eg. fewer abbreviations). This will only be called on fields that match"""
        if self.value is not None:
            if other.value is not None:
                obj = self.__class__(self.source + SOURCE_SEPARATOR + other.source)
                obj.value = self.combine_values(self.value, other.value)
                return obj
        logger.warn("Combining fields which store None")
        return self

    def set(self, value: Optional[T]) -> None:
        """Set the value to self.normalize(value)"""
        if value is not None:
            self.value = self.normalize(value)
        else:
            self.value = None

    def to_str(self) -> Optional[str]:
        """The value as a string, as it will be added to the Bibtex file"""
        if self.value is None:
            return None
        return self.to_bibtex(self.value)

    def set_str(self, value: Optional[str]) -> None:
        """Same as set, but converts the value from string to T first"""
        if value is not None:
            self.set(self.convert(value))
        else:
            self.value = None


class StrictStringField(BibtexField[str]):
    """Base class for all fields whose type is str
    Uses strict equality for comparisons"""

    @classmethod
    def convert(cls, value: str) -> str:
        return value

    @classmethod
    def normalize(cls, value: str) -> Optional[str]:
        value = value.strip()
        if value == "":
            return None
        return value


# Listify: turn a bibtex field of T into one of List[T]


def order(a: COORD_T[T], b: COORD_T[T]) -> int:
    """Weak order on optional coordinates
    Used to merge lists while attempting to preserve order"""
    if a[0][0] is not None and b[0][0] is not None:
        return a[0][0] - b[0][0]
    if a[0][1] is not None and b[0][1] is not None:
        return a[0][1] - b[0][1]
    if a[1] < b[1]:
        return -1
    if b[1] < a[1]:
        return 1
    return 0


def matrix_max(matrix: List[List[int]]) -> Optional[Tuple[int, int]]:
    """Returns x,y coordinate of max element of matrix,
    returns None if empty"""
    if matrix == [] or (matrix[0] == []):
        return None
    max_value = matrix[0][0]
    max_x = 0
    max_y = 0
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            if value > max_value:
                max_value = value
                max_x = i
                max_y = j
    return max_x, max_y


def iterate_max(matrix: List[List[int]]) -> Iterator[Tuple[int, int]]:
    """Returns the coordinates x,y of the matrix maximum
    Modifies the matrix in-place: previously seen rows and columns are
    no longer valid"""
    max_pos = matrix_max(matrix)
    while max_pos is not None:
        max_x, max_y = max_pos
        yield max_pos
        matrix[max_x] = [FIELD_NO_MATCH]
        for row in matrix:
            row[max_y] = FIELD_NO_MATCH
        max_pos = matrix_max(matrix)


LONG_LIST_DELIMITER = 5_000


def listify(
    separator_regex: str, separator: str
) -> Callable[[Type[BibtexField[T]]], Type[BibtexField[List[T]]]]:
    """Decorator that convert a bibtex field for T into a field for List[T]

    Lists are matched without order, taking the pairwise best matches first
    and returning the average match score times a factor:
    - 1 for equality (all elements have a match)
    - 1/2 for inclusion (all elements of one of the two lists match
    - 1/4 for common elements
    - 0 otherwise

    Combining values proceeds in much the same way (pairwise combines with best
    match score). Keeps the order of the longest list.

    Parsing and rendering to string is done via splitting around separator_regex
    and joining around separator"""

    def decorator(base_class: Type[BibtexField[T]]) -> Type[BibtexField[List[T]]]:
        class ListifyField(BibtexField[List[T]]):
            parent = base_class

            @classmethod
            def normalize(cls, value: List[T]) -> Optional[List[T]]:
                normalized: List[T] = []
                for val in value:
                    norm = base_class.normalize(val)
                    if norm is not None:
                        normalized.append(norm)
                if normalized:
                    return normalized
                return None

            @classmethod
            def slow_check(cls, value: List[T]) -> bool:
                return all(base_class.slow_check(x) for x in value)

            @classmethod
            def match_values(cls, a: List[T], b: List[T]) -> int:
                if len(a) * len(b) <= LONG_LIST_DELIMITER:
                    return cls.match_values_slow(a, b)
                return cls.match_values_fast(a, b)

            @classmethod
            def pairwise_scores(cls, a: List[T], b: List[T]) -> List[List[int]]:
                """returns M such that M[i][j] = match_score(a[i], b[j])"""
                scores = [[FIELD_NO_MATCH for _ in b] for _ in a]
                for i, x in enumerate(a):
                    for j, y in enumerate(b):
                        scores[i][j] = base_class.match_values(x, y)
                return scores

            @classmethod
            def match_values_slow(cls, a: List[T], b: List[T]) -> int:
                """Compute all pairwise element matches, the pick the top ones
                as common matches and removes them. This has terrible complexity,
                but list should be rather small"""
                scores = cls.pairwise_scores(a, b)
                # Count common and calc average_score
                common = 0
                common_scores = 0
                for x, y in iterate_max(scores):
                    if scores[x][y] > FIELD_NO_MATCH:
                        break
                    common += 1
                    common_scores += scores[x][y]
                return cls.compute_score(a, b, common_scores, common)

            @classmethod
            def compute_score(
                cls, a: List[T], b: List[T], common_scores: int, common: int
            ) -> int:
                """Compute the final score from the number of common elements
                and the sum of the scores"""
                average_match = common_scores // common
                # Mutliply average score by factor
                a_only = len(a) - common
                b_only = len(b) - common
                if average_match == 0:
                    average_match = 1
                if common == 0:
                    return FIELD_NO_MATCH
                if a_only == 0 and b_only == 0:
                    return average_match
                if a_only == 0 or b_only == 0:
                    return average_match // 2
                return average_match // 4

            @classmethod
            def match_values_fast(cls, a: List[T], b: List[T]) -> int:
                """faster than match_values_slow (O(n^2) instead of O(n^3)),
                used on long lists.
                May not find the best matches overall though"""
                set_b = set(b)
                common = 0
                common_scores = 0
                for elt_a in a:
                    max_score = FIELD_NO_MATCH
                    max_elt = None
                    for elt_b in b:
                        score = base_class.match_values(elt_a, elt_b)
                        if score > max_score:
                            max_score = score
                            max_elt = elt_b
                    if max_elt is not None:
                        common += 1
                        common_scores += max_score
                        set_b.remove(max_elt)
                return cls.compute_score(a, b, common_scores, common)

            @classmethod
            def combine_values(cls, a: List[T], b: List[T]) -> List[T]:
                """When two values match, choose which one to keep
                Merge elements with highest match scores first
                Then creates a new list by attempting to keep elements in order"""
                if len(a) * len(b) >= LONG_LIST_DELIMITER:
                    # Return the longest list if too long to limit complexity
                    return a if len(a) >= len(b) else b
                coords: Dict[COORD, T] = {(i, None): elt for i, elt in enumerate(a)}
                coords.update({(None, j): elt for j, elt in enumerate(b)})
                scores = cls.pairwise_scores(a, b)
                for x, y in iterate_max(scores):
                    if scores[x][y] > FIELD_NO_MATCH:
                        break
                    del coords[x, None]
                    del coords[None, y]
                    coords[x, y] = base_class.combine_values(a[x], b[y])
                keys = sorted(coords.items(), key=cmp_to_key(order))
                return [item for _, item in keys]

            @classmethod
            def to_bibtex(cls, value: List[T]) -> str:
                """Return the non-None value as a Bibtex string"""
                return separator.join(base_class.to_bibtex(x) for x in value)

            @classmethod
            def convert(cls, value: str) -> List[T]:
                converted = []
                for x in split(separator_regex, value):
                    x = x.strip()
                    if x == "":
                        continue
                    conv_x = base_class.convert(x)
                    if conv_x is not None:
                        converted.append(conv_x)
                return converted

        return ListifyField

    return decorator
