from datetime import date
from re import match, search
from typing import Dict, Optional, Union

from ..APIs.doi import DOICheck, URLCheck
from ..utils.logger import logger
from .author import Author
from .base_field import BibtexField, ListField, StrictStringField
from .constants import FIELD_FULL_MATCH, FIELD_NO_MATCH
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
    pattern = r".*\s".join(r"(|.*\s)".join(word) for word in abbrev.split())
    return match("^" + pattern, text) is not None


def pick_longest(a: str, b: str) -> str:
    """Returns the longest string, or the longest sequence of bytes in case of
    equality (to account for accents)"""
    if len(a) > len(b):
        return a
    if len(b) > len(a):
        return b
    if len(bytes(a, "utf8")) >= len(bytes(b, "utf8")):
        return a
    return b


class BasicStringField(StrictStringField):
    """Class for most fields, including title.
    - Normalization trims leading/ending spaces and converts to unicode
    - Three match levels:
       - FIELD_FULL_MATCH if match in lowercase, excluding accent normalize_str_weak
       - FIELD_FULL_MATCH / 2 if match in lowercase, all non alpha-numeric normalize_str
       - FIELD_NO_MATCH if match using normalize_str
    - combining just picks the left argument
    """

    @classmethod
    def match_values(cls, a: str, b: str) -> int:
        if normalize_str_weak(a) == normalize_str_weak(b):
            return FIELD_FULL_MATCH
        if normalize_str(a) == normalize_str(b):
            return FIELD_FULL_MATCH // 2
        return FIELD_NO_MATCH


class AbbreviatedStringField(StrictStringField):
    """Class for fields that are commonly abbreviated:
    - Normalization trims leading/ending spaces and converts to unicode
    - Four match levels:
       - FIELD_FULL_MATCH if match in lowercase, excluding accent normalize_str_weak
       - FIELD_FULL_MATCH * 2 / 3 if match in lowercase, all non alpha-numeric normalize_str
       - FIELD_FULL_MATCH / 3 if one of the normalize_str values abbreviates the other through is_abbrev
       - FIELD_NO_MATCH if match using normalize_str
    - combining just picks the left argument
    """

    @classmethod
    def match_values(cls, a: str, b: str) -> int:
        if normalize_str_weak(a) == normalize_str_weak(b):
            return FIELD_FULL_MATCH
        norm_a = normalize_str(a)
        norm_b = normalize_str(b)
        if norm_a == norm_b:
            return FIELD_FULL_MATCH * 2 // 3
        if is_abbrev(norm_a, norm_b) or is_abbrev(norm_b, norm_a):
            return FIELD_FULL_MATCH // 3
        return FIELD_NO_MATCH

    @classmethod
    def combine_values(cls, a: str, b: str) -> str:
        return pick_longest(a, b)


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
    def slow_check(cls, doi: str, entry_name: str) -> bool:
        """Query doi.org API to check DOI exists"""
        try:
            doi_checker = DOICheck(doi)
            return doi_checker.query() is True
        except Exception as err:
            logger.traceback(
                f"Uncaught exception when checking DOI resolution\n"
                f"Entry = {entry_name}\n"
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
    def slow_check(cls, value: str, entry_name: str) -> bool:
        try:
            checker = URLCheck(value)
            return checker.query() is not None
        except Exception as err:
            logger.traceback(
                f"Uncaught exception when checking URL resolution\n"
                f"Entry = {entry_name}\n"
                f"URL = {value}\n\n"
                "As a result, this URL will NOT be added to the entry",
                err,
            )
        return False


class NameBaseField(BibtexField[Author]):
    """
    Class for author and editor field, list of Author (separate first and last name)
    Merging keeps longest names, So "J. Doe" and "John Doe" merge to the later
    """

    @classmethod
    def to_bibtex(cls, value: Author) -> str:
        """The value as a string, as it will be added to the Bibtex file"""
        return Author.to_bibtex(value)

    @classmethod
    def convert(cls, value: str) -> Optional[Author]:
        return Author.from_name(value)

    @classmethod
    def match_values(cls, a: Author, b: Author) -> int:
        if normalize_str(a.lastname) != normalize_str(b.lastname):
            return FIELD_NO_MATCH
        if a.firstnames is None or b.firstnames is None:
            return FIELD_FULL_MATCH // 2
        if normalize_str(a.firstnames) == normalize_str(b.firstnames):
            return FIELD_FULL_MATCH
        if is_abbrev(a.firstnames, b.firstnames) or is_abbrev(b.firstnames, a.firstnames):
            return 3 * FIELD_FULL_MATCH // 4
        return FIELD_NO_MATCH

    @classmethod
    def combine_values(cls, a: Author, b: Author) -> Author:
        lastname = a.lastname
        if a.firstnames is not None and b.firstnames is not None:
            firstname = pick_longest(a.firstnames, b.firstnames)
            return Author(lastname, firstname)
        if a.firstnames is not None:
            return Author(lastname, a.firstnames)
        if b.firstnames is not None:
            return Author(lastname, b.firstnames)
        return Author(lastname, None)


class NameField(ListField[Author]):
    separator: str = " and "
    separator_regex: str = r"\band\b"
    base_class = NameBaseField


class ISSNBaseField(StrictStringField):
    """ISSN field, normalized to 'nnnn-nnnX' where n is 0-9 and X is 0-9 or X
    Normalization checks the check digit (sum must be 0 modulo 11) and enforces
    a single dash between two four-digit groups.
    """

    @classmethod
    def normalize(cls, value: str) -> Optional[str]:
        value = normalize_str(value.lower().replace("issn", "")).replace(" ", "")
        if len(value) != 8:
            return None
        if match(r"[0-9]{7}[0-9x]", value) is None:
            return None
        # Last digit is a check code
        sum = 0
        for i in range(8):
            sum += (8 - i) * int(value[i].replace("x", "10"))
        if sum % 11 != 0:
            return None
        return value[:4] + "-" + value[4:].upper()


class ISSNField(ListField[str]):
    separator: str = ", "
    separator_regex: str = r"\,"
    base_class = ISSNBaseField


class ISBNField(StrictStringField):
    """ISBN field, nnn-nnnnnnnnnn
    Converts 10 digit ISBN to 13 digit version
    Normalization removes extra dashes and verifies check digits
    """

    @staticmethod
    def check_digit_13(values: str) -> str:
        sum = 0
        weight = 1
        for i in range(12):
            sum += int(values[i]) * weight
            weight = 3 if weight == 1 else 1
        sum = sum % 10
        if sum == 0:
            return "0"
        return str(10 - sum)

    @classmethod
    def normalize(cls, value: str) -> Optional[str]:
        value = normalize_str(value.lower().replace("isbn", "")).replace(" ", "")
        if len(value) not in {10, 13}:
            return None
        if match(r"([0-9]{9}[0-9x])|([0-9]{13})", value) is None:
            return None

        if len(value) == 10:
            # Last digit is a check code
            sum = 0
            for i in range(10):
                sum += (10 - i) * int(value[i].replace("x", "10"))
            if sum % 11 != 0:
                return None
            # Convert to 13 digit normal form
            value = "978" + value
            value = value[:12] + cls.check_digit_13(value)
        else:
            if value[-1] != cls.check_digit_13(value):
                return None
        return value[:3] + "-" + value[3:].upper()


class MonthField(StrictStringField):
    """Normalize a month to "1" - "12",
    Recognizes english and locale abbreviations
    """

    @staticmethod
    def months_format(month: int, format: str) -> str:
        """Localized month format"""
        return date(2001, month, 1).strftime(format)

    @staticmethod
    def get_locale_months() -> Dict[str, int]:
        mapping = {}
        for month in range(1, 13):
            for format in ("%B", "%b"):  # "%m", "%-m"
                mapping[MonthField.months_format(month, format).lower()] = month
        return mapping

    EN_MONTHS = {
        "january": 1,
        "jan": 1,
        "01": 1,
        "1": 1,
        "february": 2,
        "feb": 2,
        "02": 2,
        "2": 2,
        "march": 3,
        "mar": 3,
        "03": 3,
        "3": 3,
        "april": 4,
        "apr": 4,
        "04": 4,
        "4": 4,
        "may": 5,
        "05": 5,
        "5": 5,
        "june": 6,
        "jun": 6,
        "06": 6,
        "6": 6,
        "july": 7,
        "jul": 7,
        "07": 7,
        "7": 7,
        "august": 8,
        "aug": 8,
        "08": 8,
        "8": 8,
        "september": 9,
        "sep": 9,
        "09": 9,
        "9": 9,
        "october": 10,
        "oct": 10,
        "10": 10,
        "november": 11,
        "nov": 11,
        "11": 11,
        "december": 12,
        "dec": 12,
        "12": 12,
    }

    @classmethod
    def normalize(cls, value: str) -> Optional[str]:
        """Tries to normalize a month to it's number "1" to "12"
        returns month unchanged if unsuccessful"""
        months = cls.EN_MONTHS.copy()
        months.update(cls.get_locale_months())
        norm = normalize_str(value)
        if norm in months:
            return str(months[norm])
        return None


class YearField(StrictStringField):
    """Normalize a year to a number between 100 and current_year + 10"""

    @classmethod
    def normalize(cls, value: str) -> Optional[str]:
        value = value.strip()
        if value.isnumeric():
            y = int(value)
            max = date.today().year + 10
            if y <= 100 or max <= y:
                return None
            return str(y)
        return None


PAGES_SEPARATOR = "--"


# PagesType = Union[
#     Tuple[Literal["int"], Literal["range"], int, int],
#     Tuple[Literal["int"], Literal["single"], int],
#     Tuple[Literal["roman-lower"], Literal["range"], str, str],
#     Tuple[Literal["roman-lower"], Literal["single"], str],
#     Tuple[Literal["roman-upper"], Literal["range"], str, str],
#     Tuple[Literal["roman-upper"], Literal["single"], str],
#     Tuple[Literal["unknown"], Literal["range"], str, str],
#     Tuple[Literal["unknown"], Literal["single"], str],
# ]


class PagesBaseField(StrictStringField):
    "Normalize pages to list of n--n or n"

    # ROMAN_DIGITS = {"M": 1000, "D": 500, "C": 100, "L": 50, "X": 10, "V": 5, "I": 1}

    # @classmethod
    # def is_roman(cls, string: str) -> bool:
    #     return not set(string.upper()).difference(cls.ROMAN_DIGITS)

    # @classmethod
    # def roman_to_int(cls, string: str) -> int:
    #     """
    #     Convert a roman number to an integer
    #     Solution from https://stackoverflow.com/a/61719273
    #     """
    #     res = 0
    #     p = "I"
    #     string = string.upper()
    #     for c in string[::-1]:
    #         res = (
    #             res - cls.ROMAN_DIGITS[c]
    #             if cls.ROMAN_DIGITS[c] < cls.ROMAN_DIGITS[p]
    #             else res + cls.ROMAN_DIGITS[c]
    #         )
    #         p = c
    #     return res

    @classmethod
    def normalize(cls, value: str) -> Optional[str]:
        separators = r"(?:(?:\-+)|–)"
        regex = r"^\s*(\S+)\s*" + separators + r"\s*(\S+)\s*$"
        result = match(regex, value)
        if result is None:
            return value.strip()
        str_a = result.group(1).strip()
        str_b = result.group(2).strip()
        if str_a == str_b:
            return str_a
        return str_a + PAGES_SEPARATOR + str_b


class PagesField(ListField[str]):
    separator: str = ", "
    separator_regex: str = r"\,"
    base_class = PagesBaseField

    def from_pair(self, a: Union[str, int, None], b: Union[str, int, None]) -> None:
        """Set the value from a pair of first, last page"""
        if a is None and b is None:
            self.value = None
        elif b is None:
            self.value = [str(a).strip()]
        elif a is None:
            self.value = [str(b).strip()]
        else:
            str_a = str(a).strip()
            str_b = str(b).strip()
            if str_a == str_b:
                self.value = [str_a]
            else:
                self.value = [str_a + PAGES_SEPARATOR + str_b]
