from re import match, search
from typing import Optional

from ..APIs.doi import DOICheck, URLCheck
from ..utils.logger import logger
from .author import Author
from .base_field import (
    FIELD_FULL_MATCH,
    FIELD_NO_MATCH,
    BibtexField,
    StrictStringField,
    listify,
)
from .normalize import normalize_str, normalize_str_weak, normalize_url


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


class BasicStringField(StrictStringField):
    """Class for most fields, including title.
    - Normalization trims leading/ending spaces
    - Two match levels:
       - FIELD_FULL_MATCH if match in lowercase, excluding accent normalize_str_weak
       - FIELD_NO_MATCH if match using normalize_str
    """

    @classmethod
    def match_values(cls, a: str, b: str) -> int:
        if normalize_str_weak(a) == normalize_str_weak(b):
            return FIELD_FULL_MATCH
        if normalize_str(a) == normalize_str(b):
            return FIELD_FULL_MATCH // 2
        return FIELD_NO_MATCH


class DOIField(StrictStringField):
    """Class for DOI field
    Normalized to 10.nnnnn/xxxxxxxxxxxx, in lowercase
    Checks DOI exists by querying doi.org/<doi> and following redirections"""

    DOI_REGEX = r"(10\.\d{4,5}\/[\S]+[^;,.\s])$"

    @classmethod
    def normalize(cls, doi: str) -> Optional[str]:
        """Returns doi to canonical form (i.e. removing url)"""
        match = search(DOIField.DOI_REGEX, doi)
        if match is not None:
            return match.group(1).lower()  # DOI's are case insensitive
        return None

    @classmethod
    def slow_check(cls, doi: str) -> bool:
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


class URLField(StrictStringField):
    """Class for DOI field
    Normalized to https://domain/path decoded + reencoded to ensure same encoding
    Checks the URL exists by simple query"""

    @classmethod
    def normalize(cls, value: str) -> Optional[str]:
        url = normalize_url(value)
        if url is not None:
            return "https://" + url[0] + url[1]
        return None

    @classmethod
    def slow_check(cls, value: str) -> bool:
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


@listify(r"\s+and\s+", " and ")
class NameField(BibtexField[Author]):
    """Class for author and editor field, list of names"""

    @classmethod
    def to_bibtex(cls, value: Author) -> str:
        """The value as a string, as it will be added to the Bibtex file"""
        return Author.to_bibtex(value)

    @classmethod
    def convert(cls, value: str) -> Optional[Author]:
        return Author.from_name(value)

    # @classmethod
    # def match_values(cls, a: Author, b: Author) -> int:
    #     authors_common, authors_a, authors_b = common_authors(a, b)
    #     if authors_common == 0 and authors_a > 0 and authors_b > 0:
    #         # No common authors despite some authors being known on both sides
    #         return FIELD_NO_MATCH
    #     if authors_common != 0:
    #         if authors_common == authors_a and authors_common == authors_b:
    #             return FIELD_FULL_MATCH
    #         elif authors_common == authors_a or authors_common == authors_b:
    #             return FIELD_FULL_MATCH // 2
    #         else:
    #             return FIELD_FULL_MATCH // 4
    #     return super().match_values(a, b)


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

    # address: BibtexField[str] = BasicStringField()
    # annote: BibtexField[str] = BasicStringField()
    # author: BibtexField[List[Author]] = NameField()
    # booktitle: Optional[str]
    # chapter: Optional[str]
    # doi: BibtexField[str] = DOIField()
    # edition: Optional[str]
    # editor: BibtexField[List[Author]] = NameField()
    # howpublished: BibtexField[str] = BasicStringField()
    # institution: Optional[str]
    # issn: Optional[str]
    # isbn: Optional[str]
    # journal: Optional[str]
    # month: Optional[str]  # Number in "1" .. "12"
    # note: Optional[str]
    # number: Optional[str]
    # organization: Optional[str]
    # pages: Optional[str]
    # publisher: Optional[str]
    # school: Optional[str]
    # series: Optional[str]
    # title: BibtexField[str] = BasicStringField()
    # ~type: BibtexField[str] = BasicStringField()
    # url: BibtexField[str] = URLField()
    # volume: Optional[str]
    # year: Optional[str]
