"""
Functions used to normalize bibtex fields
"""

import unicodedata
from datetime import date
from re import search
from typing import Optional

from ..utils.constants import EntryType


def has_field(entry: EntryType, field: str) -> bool:
    """Check if a given entry has non empty field"""
    return field in entry and entry[field] != ""


def get_field(entry: EntryType, field: str) -> Optional[str]:
    """Check if given field exists and is non-empty
    if so, removes braces and returns it"""
    if has_field(entry, field):
        plain = entry[field].replace("{", "").replace("}", "").strip()
        if plain:
            return plain
    return None


def strip_accents(s):
    """replace accented characters with their non-accented variants"""
    # Solution from https://stackoverflow.com/a/518232
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def normalize_str(string: str) -> str:
    """Normalize string for decent comparison
    Converts to lower case
    Replaces all non alpha-numeric characters with spaces
    Removes duplicate spaces"""
    res = ""
    prev_space = False
    for x in strip_accents(string):
        if x.isalnum():
            res += x
            prev_space = False
        elif not prev_space:
            res += " "
            prev_space = True
    return res.lower().strip()


DOI_REGEX = r"(10\.\d{4,5}\/[\S]+[^;,.\s])$"


def normalize_doi(doi_or_url: Optional[str]) -> Optional[str]:
    """Returns doi to canonical form (i.e. removing url)"""
    if doi_or_url is not None:
        match = search(DOI_REGEX, doi_or_url)
        if match is not None:
            return match.group(1).lower()  # DOI's are case insensitive
    return None


def months_format(month: int, format: str):
    """Localized month format"""
    return date(2001, month, 1).strftime(format)


def get_locale_months() -> dict[str, int]:
    mapping = {}
    for month in range(1, 13):
        for format in ("%B", "%b"):  # "%m", "%-m"
            mapping[months_format(month, format).lower()] = month
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


def normalize_month(month: str) -> str:
    """Tries to normalize a month to it's number "1" to "12"
    returns month unchanged if unsuccessful"""
    months = EN_MONTHS.copy()
    months.update(get_locale_months())
    norm = normalize_str(month)
    if norm in months:
        return str(months[norm])
    return month
