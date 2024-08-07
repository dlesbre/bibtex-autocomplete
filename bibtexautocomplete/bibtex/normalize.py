"""
Functions used to normalize bibtex fields
"""

import unicodedata
from re import search, sub
from typing import Optional, Tuple
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlsplit

from bibtexparser.latexenc import latex_to_unicode

from ..utils.constants import EntryType
from ..utils.logger import logger


def make_plain(value: Optional[str]) -> Optional[str]:
    """Returns a plain version of the field (remove redundant braces)
    returns None if the field is None or empty string"""
    if value is not None:
        plain = value.replace("{", "").replace("}", "").strip()
        if plain != "" and not plain.isspace():
            return plain
    return None


def has_data(value: Optional[str]) -> bool:
    """Return true if the given value contains data, false otherwise"""
    return make_plain(value) is not None


def get_field(entry: EntryType, field: str) -> Optional[str]:
    """Check if given field exists and is non-empty
    if so, removes braces and returns it"""
    if field in entry:
        return make_plain(entry[field])
    return None


def has_field(entry: EntryType, field: str) -> bool:
    """Check if a given entry has non empty field"""
    return has_data(get_field(entry, field))


def strip_accents(string: str) -> str:
    """replace accented characters with their non-accented variants"""
    # Solution from https://stackoverflow.com/a/518232
    return "".join(c for c in unicodedata.normalize("NFD", string) if unicodedata.category(c) != "Mn")


def normalize_str_weak(string: str, from_latex: bool = True) -> str:
    """Converts to lower case, strips accents,
    replace tabs and newline with spaces,
    removes duplicate spaces"""
    if from_latex:
        string = latex_to_unicode(string)
    string = strip_accents(string).lower()
    return sub(r"\s+", " ", string)


def normalize_str(string: str) -> str:
    """Normalize string for decent comparison
    Converts to lower case, strips accents
    Replaces all non alpha-numeric characters with spaces
    Removes duplicate spaces"""
    string = latex_to_unicode(string)
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


def normalize_url(url: str, previous: Optional[str] = None) -> Optional[Tuple[str, str]]:
    """Splits and url into domain/path
    Returns none if url is not valid"""
    url_copy = url
    if previous is not None:
        # resolve relative URLs
        url = urljoin(previous, url)
    split = urlsplit(url)
    if split.netloc == "" or split.scheme == "":
        logger.debug(f"INVALID URL: {url_copy}, FROM {previous}")
        return None
    domain = split.netloc
    path = quote(split.path, safe="/:+")
    if split.query != "":
        path += "?" + urlencode(parse_qsl(split.query))
    if split.fragment != "":
        path += "#" + split.fragment
    return domain, path
