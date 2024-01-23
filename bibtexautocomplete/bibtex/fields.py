from re import match, search
from typing import Generic, List, Optional, Set, Tuple, TypeVar

from ..APIs.doi import DOICheck, URLCheck
from ..utils.logger import logger
from .author import Author
from .normalize import normalize_str, normalize_str_weak, normalize_url

T = TypeVar("T")


FIELD_FULL_MATCH = 100
FIELD_NO_MATCH = 0


def is_abbrev(abbrev: str, text: str) -> bool:
    """Checks if abbrev is an abbreviation of text
    - both must be lowercase with no punctuation
    - Only detects sequences at start of words:
      >>> is_abbrev("proc acm", "proceedings of the association for computer machinery")
      True
      >>> is_abbrev("jr", "junior")
      False
      >>> is_abbrev("kph", "Kopenhaven")
      False
    """
    # Algorithm from https://stackoverflow.com/a/7332054
    pattern = r"(|.*\s)".join(abbrev)
    return match("^" + pattern, text) is not None


class BibtexField(Generic[T]):
    """A bibtex field, represented by type T
    for most T = str, but there are some exceptions:
    - authors: T = List[Author]
    - year, month, issn, isbn: T = int
    """

    value: Optional[T]

    def __init__(self) -> None:
        self.value = None

    def normalize(self, value: T) -> Optional[T]:
        """Return a normal representation of the entry
        Can return None if invalid format"""
        return value

    def slow_check(self, value: T) -> bool:
        """Performs a slow check (e.g. query URL to ensure it resolves)
        Only done if we want to use this in our field"""
        return True

    def slow_check_none(self) -> bool:
        """Performs a slow check (e.g. query URL to ensure it resolves)
        Only done if we want to use this in our field"""
        if self.value is None:
            return False
        return self.slow_check(self.value)

    def match_values(self, a: T, b: T) -> int:
        """returns a match score: 0 <= score <= FIELD_FULL_MATCH"""
        if a == b:
            return FIELD_FULL_MATCH
        return FIELD_NO_MATCH

    def matches(self, other: "BibtexField[T]") -> Optional[int]:
        """returns a match score: 0 <= score <= FIELD_FULL_MATCH
        Returns None if one of the values is None"""
        if self.value is None or other.value is None:
            return None
        return self.match_values(self.value, other.value)

    def combine(self, other: "BibtexField[T]") -> "BibtexField[T]":
        """Merges both fields to return the one with maximum information
        (eg. fewer abbreviations). This will only be called on fields that match"""
        return self

    def set(self, value: Optional[T]) -> None:
        """Set the value to self.normalize(value)"""
        if value is not None:
            self.value = self.normalize(value)
        else:
            self.value = None

    def to_bibtex(self, value: T) -> str:
        """Return the non-None value as a Bibtex string"""
        return str(value)

    def to_str(self) -> Optional[str]:
        """The value as a string, as it will be added to the Bibtex file"""
        if self.value is None:
            return None
        return self.to_bibtex(self.value)

    def convert(self, value: str) -> T:
        raise NotImplementedError("override in child classes")

    def set_str(self, value: Optional[str]) -> None:
        """Same as set, but converts the value from string to T first"""
        if value is not None:
            self.set(self.convert(value))
        else:
            self.value = None


class StringField(BibtexField[str]):
    """Base class for all fields whose type is str"""

    def convert(self, value: str) -> str:
        return value

    def normalize(self, value: str) -> Optional[str]:
        value = value.strip()
        if value == "":
            return None
        return value


class BasicStringField(StringField):
    """Class for most fields, including title.
    - Normalization trims leading/ending spaces
    - Two match levels:
       - FIELD_FULL_MATCH if match in lowercase, excluding accent normalize_str_weak
       - FIELD_NO_MATCH if match using normalize_str
    """

    def match_values(self, a: str, b: str) -> int:
        if normalize_str_weak(a) == normalize_str_weak(b):
            return FIELD_FULL_MATCH
        if normalize_str(a) == normalize_str(b):
            return FIELD_FULL_MATCH // 2
        return FIELD_NO_MATCH


class DOIField(StringField):
    """Class for DOI field
    Normalized to 10.nnnnn/xxxxxxxxxxxx, in lowercase
    Checks DOI exists by querying doi.org/<doi> and following redirections"""

    DOI_REGEX = r"(10\.\d{4,5}\/[\S]+[^;,.\s])$"

    def normalize(self, doi: str) -> Optional[str]:
        """Returns doi to canonical form (i.e. removing url)"""
        match = search(self.DOI_REGEX, doi)
        if match is not None:
            return match.group(1).lower()  # DOI's are case insensitive
        return None

    def slow_check(self, doi: str) -> bool:
        """Query doi.org API to check DOI exists"""
        try:
            doi_checker = DOICheck(doi)
            return doi_checker.query() is True
        except Exception as err:
            logger.traceback(
                f"Uncaught exception when checking DOI resolution\n"
                f"Entry = {id}\n"
                f"DOI = {doi}\n\n"
                "As a result, this DOI will NOT be added to the entry",
                err,
            )
            return False


class URLField(StringField):
    """Class for DOI field
    Normalized to https://domain/path decoded + reencoded to ensure same encoding
    Checks the URL exists by simple query"""

    def normalize(self, value: str) -> Optional[str]:
        url = normalize_url(value)
        if url is not None:
            return "https://" + url[0] + url[1]
        return None

    def slow_check(self, value: str) -> bool:
        try:
            checker = URLCheck(value)
            return checker.query() is not None
        except Exception as err:
            logger.traceback(
                f"Uncaught exception when checking URL resolution\n"
                f"Entry = {id}\n"
                f"URL = {value}\n\n"
                "As a result, this URL will NOT be added to the entry",
                err,
            )
        return False


def author_set(authors: List[Author]) -> Set[str]:
    """Returns the set of normalized author lastname from entry
    I.E. lowercase last names, with spaces removed"""
    last_names: Set[str] = set()
    for author in authors:
        normalized = normalize_str(author.lastname).replace(" ", "")
        if normalized != "":
            last_names.add(normalized)
    return last_names


def common_authors(a: List[Author], b: List[Author]) -> Tuple[int, int, int]:
    """Returns:
    - number of common authors;
    - number of authors of a only,
    - number of authors of b only"""
    authors_a = author_set(a)
    authors_b = author_set(b)
    common = authors_a.intersection(authors_b)
    return len(common), len(authors_a), len(authors_b)


class NameField(BibtexField[List[Author]]):
    """Class for author and editor field, list of names"""

    def normalize(self, value: List[Author]) -> Optional[List[Author]]:
        if len(value) == 0:
            return None
        return value

    def to_bibtex(self, value: List[Author]) -> str:
        """The value as a string, as it will be added to the Bibtex file"""
        return Author.list_to_bibtex(value)

    def convert(self, value: str) -> List[Author]:
        return Author.from_namelist(value)

    def match_values(self, a: List[Author], b: List[Author]) -> int:
        authors_common, authors_a, authors_b = common_authors(a, b)
        if authors_common == 0 and authors_a > 0 and authors_b > 0:
            # No common authors despite some authors being known on both sides
            return FIELD_NO_MATCH
        if authors_common != 0:
            if authors_common == authors_a and authors_common == authors_b:
                return FIELD_FULL_MATCH
            elif authors_common == authors_a or authors_common == authors_b:
                return FIELD_FULL_MATCH // 2
            else:
                return FIELD_FULL_MATCH // 4
        return super().match_values(a, b)


class BibtexEntry:
    """A class to encapsulate bibtex entries
    Avoids spelling errors in field names
    and performs sanity checks

    Note: sanity check are performed when setting/getting attributes
    >>> entry.doi.set("10.1234/123456")
    >>> entry.doi.set("not_a_doi") # Invalid format, set DOI to None
    >>> entry.doi.to_str() # None
    They are not performed on initialization !
    >>> entry = BibtexEntry({'doi': 'not_a_doi'})
    >>> entry.doi.to_str() # None
    >>> entry.to_entry() # {'doi': 'not_a_doi'}

    Some fields have special treatment:
    - author and editor return/are set by a list of authors instead of a string
    - doi is formatted on get/set to remove leading url
    - month is formatted to "1" -- "12" if possible (recognizes "jan", "FeB.", "March"...)
    """

    address: BibtexField[str] = BasicStringField()
    annote: BibtexField[str] = BasicStringField()
    author: BibtexField[List[Author]] = NameField()
    booktitle: Optional[str]
    chapter: Optional[str]
    doi: BibtexField[str] = DOIField()
    edition: Optional[str]
    editor: BibtexField[List[Author]] = NameField()
    howpublished: BibtexField[str] = BasicStringField()
    institution: Optional[str]
    issn: Optional[str]
    isbn: Optional[str]
    journal: Optional[str]
    month: Optional[str]  # Number in "1" .. "12"
    note: Optional[str]
    number: Optional[str]
    organization: Optional[str]
    pages: Optional[str]
    publisher: Optional[str]
    school: Optional[str]
    series: Optional[str]
    title: BibtexField[str] = BasicStringField()
    type: BibtexField[str] = BasicStringField()
    url: BibtexField[str] = URLField()
    volume: Optional[str]
    year: Optional[str]
