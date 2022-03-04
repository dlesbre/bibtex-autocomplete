"""
Functions to read/write/manipulate bibtex databases
"""

from datetime import date
from typing import Iterator, List, Optional

from bibtexparser import customization
from bibtexparser.bibdatabase import BibDatabase, UndefinedString
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter

from .defs import EntryType, extract_doi, logger, str_normalize

# =================================================
# § Bibtexparser wrappers
# =================================================


parser = BibTexParser(common_strings=True)
# Keep non standard entries if present
parser.ignore_nonstandard_types = False

writer = BibTexWriter()
writer.indent = "\t"
writer.add_trailing_comma = True
writer.order_entries_by = ("author", "year", "title")
writer.display_order = ("author", "title")

PLAIN_PREFIX = "plain_"


def remove_plain_fields(entry: EntryType) -> None:
    """Removes the plain_ fields from an entry"""
    to_delete = [field for field in entry if field.startswith(PLAIN_PREFIX)]
    for to_del in to_delete:
        del entry[to_del]


def write(database: BibDatabase) -> str:
    """Transform the database to a bibtex string"""
    for entry in database.entries:
        remove_plain_fields(entry)
    return writer.write(database).strip()


def write_to(filepath, database: BibDatabase) -> None:
    output = write(database)
    if filepath is None:
        print(output)
    else:
        with open(filepath, "w") as file:
            file.write(output)


def read(filepath) -> BibDatabase:
    """reads the given file, parses and normalizes it"""
    # Read and parse the file
    try:
        with open(filepath, "r") as file:
            database = parser.parse_file(file)
    except IOError as err:
        logger.critical(f"Error when reading '{str(filepath)}': {err}")
        exit(1)
    except UndefinedString as err:
        logger.critical(
            f"Error when parsing bibtex '{str(filepath)}': undefined string '{err}'"
        )
        exit(1)

    # Normalize bibliography
    for entry in database.entries:
        customization.convert_to_unicode(entry)
        customization.doi(entry)
        # customization.link(entry)
        # adds plain_XXX for all fields, without nested braces
        # customization.add_plaintext_fields(entry)

    return database


def get_plain(entry: EntryType, field: str) -> Optional[str]:
    if has_field(entry, field):
        plain = entry[field].replace("{", "").replace("}", "").strip()
        if plain:
            return plain
    return None


AUTHOR_JOIN = " and "


class Author:
    firstnames: Optional[str]
    lastname: str

    def __init__(self, lastname: str, firstnames: Optional[str]) -> None:
        self.lastname = lastname
        self.firstnames = firstnames

    def __repr__(self) -> str:
        return f"Author({self.lastname}, {self.firstnames})"

    def to_bibtex(self) -> str:
        if self.firstnames is not None:
            return f"{self.lastname}, {self.firstnames}"
        return self.lastname

    def __eq__(self, other) -> bool:
        return self.firstnames == other.firstnames and self.lastname == other.lastname

    @staticmethod
    def from_name(name: Optional[str]) -> "Optional[Author]":
        """Reads a bibtex string into a author name"""
        if name is None or name == "" or name.isspace():
            return None
        name = name.replace("\n", "").strip()
        if "," in name:
            namesplit = name.split(",", 1)
            last = namesplit[0].strip()
            firsts = [i.strip() for i in namesplit[1].split()]
        else:
            namesplit = name.split()
            last = namesplit.pop()
            firsts = [i.replace(".", ". ").strip() for i in namesplit]
        if last in ["jnr", "jr", "junior"]:
            last = firsts.pop()
        for item in firsts:
            if item in ["ben", "van", "der", "de", "la", "le"]:
                last = firsts.pop() + " " + last
        first = " ".join(firsts) if firsts else None
        return Author(last, first)

    @classmethod
    def from_namelist(cls, authors: str) -> "List[Author]":
        """Return a list of 'first name', 'last name' for authors"""
        result = []
        for name in authors.replace("\n", " ").replace("\t", " ").split(AUTHOR_JOIN):
            aut = cls.from_name(name)
            if aut is not None:
                result.append(aut)
        return result


def has_field(entry: EntryType, field: str) -> bool:
    """Check if a given entry has non empty field"""
    return field in entry and entry[field] != ""


def get_entries(db: BibDatabase) -> List[EntryType]:
    return db.entries


class FieldNames:
    """constants for bibtex field names"""

    ADDRESS = "address"
    ANNOTE = "annote"
    AUTHOR = "author"
    BOOKTITLE = "booktitle"
    CHAPTER = "chapter"
    DOI = "doi"
    EDITION = "edition"
    EDITOR = "editor"
    HOWPUBLISHED = "howpublished"
    INSTITUTION = "institution"
    ISSN = "issn"
    ISBN = "isbn"
    JOURNAL = "journal"
    MONTH = "month"
    NOTE = "note"
    NUMBER = "number"
    ORGANIZATION = "organization"
    PAGES = "pages"
    PUBLISHER = "publisher"
    SCHOOL = "school"
    SERIES = "series"
    TITLE = "title"
    TYPE = "type"
    URL = "url"
    VOLUME = "volume"
    YEAR = "year"


# Set of all fields
FieldNamesSet: set[str] = {
    value
    for attr, value in vars(FieldNames).items()
    if isinstance(value, str) and "_" not in attr and attr.upper() == attr
}

# Set of fields with sanitized inputs
SpecialFields: set[str] = {
    "author",
    "doi",
    "editor",
    "month",
}


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
    norm = str_normalize(month)
    if norm in months:
        return str(months[norm])
    return month


class BibtexEntry:
    """A class to encapsulate bibtex entries
    Avoids spelling errors in field names
    and performs sanity checks

    Note: sanity check are performed when setting/getting attributes
    >>> entry.doi = "10.1234/123456"
    >>> entry.doi = "not_a_doi" # Will not do anything, fails quietly
    >>> entry.doi # "10.1234/123456"
    They are not performed on initialization !
    >>> entry = BibtexEntry({'doi': 'not_a_doi'})
    >>> entry.doi # None
    >>> entry.to_entry() # {'doi': 'not_a_doi'}

    Some fields have special treatment:
    - author and editor return/are set by a list of authors instead of a string
    - doi is formatted on get/set to remove leading url
    - month is formatted to "1" -- "12" if possible (recognizes "jan", "FeB.", "March"...)
    """

    address: Optional[str]
    annote: Optional[str]
    author: List[Author]
    booktitle: Optional[str]
    chapter: Optional[str]
    doi: Optional[str]
    edition: Optional[str]
    editor: List[Author]
    howpublished: Optional[str]
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
    title: Optional[str]
    type: Optional[str]
    url: Optional[str]
    volume: Optional[str]
    year: Optional[str]

    _author: List[Author]
    _editor: List[Author]

    _entry: EntryType

    def __init__(self, entry: Optional[EntryType] = None):
        """Init is not thread safe"""
        if entry is None:
            self._entry = dict()
        else:
            self._entry = entry.copy()

    def __getattribute__(self, attr_name: str):
        """Performs checks when returning Bibtex fields"""
        if attr_name in FieldNamesSet:
            if attr_name in SpecialFields:
                return getattr(self, "get_" + attr_name)()
            return get_plain(self._entry, attr_name)
        return super().__getattribute__(attr_name)

    def __setattr__(self, attr_name: str, value):
        """Performs checks when returning Bibtex fields"""
        if attr_name in FieldNamesSet:
            if attr_name in SpecialFields:
                return getattr(self, "set_" + attr_name)(value)
            else:
                self.entry[attr_name] = value
            return None
        return super().__setattr__(attr_name, value)

    def __delattr__(self, attr_name: str) -> None:
        if attr_name in FieldNamesSet:
            if attr_name in self.entry:
                del self.entry[attr_name]
            return
        return super().__delattr__(attr_name)

    def __contains__(self, field) -> bool:
        """Is the given field non empty in this entry?"""
        return field in FieldNamesSet and has_field(self._entry, field)

    def __iter__(self) -> Iterator[tuple[str, str]]:
        """Iterates through the fields of self"""
        for key, val in self._entry.items():
            if key in FieldNamesSet:
                yield key, val

    def get_author(self) -> List[Author]:
        """Formats entry['author'] into Author list"""
        authors = get_plain(self._entry, FieldNames.AUTHOR)
        if authors is not None:
            return Author.from_namelist(authors)
        return []

    def get_editor(self) -> List[Author]:
        """Formats entry['editor'] into Author list"""
        authors = get_plain(self._entry, FieldNames.EDITOR)
        if authors is not None:
            return Author.from_namelist(authors)
        return []

    def set_author(self, authors: List[Author]) -> None:
        """set entry['author']"""
        if len(authors) == 0:
            if FieldNames.AUTHOR in self._entry:
                del self._entry[FieldNames.AUTHOR]
        else:
            self._entry[FieldNames.AUTHOR] = AUTHOR_JOIN.join(
                x.to_bibtex() for x in authors
            )

    def set_editor(self, authors: List[Author]) -> None:
        """set entry['editor']"""
        if len(authors) == 0:
            if FieldNames.EDITOR in self._entry:
                del self._entry[FieldNames.EDITOR]
        else:
            self._entry[FieldNames.EDITOR] = AUTHOR_JOIN.join(
                x.to_bibtex() for x in authors
            )

    def get_doi(self) -> Optional[str]:
        """get the doi without leading url"""
        return extract_doi(get_plain(self._entry, FieldNames.DOI))

    def set_doi(self, doi: str) -> None:
        """get the doi without leading url"""
        value = extract_doi(doi)
        if value is None:
            if FieldNames.DOI in self._entry:
                del self._entry[FieldNames.DOI]
        else:
            self._entry[FieldNames.DOI] = value

    def get_month(self) -> Optional[str]:
        month = get_plain(self._entry, FieldNames.MONTH)
        if month is None:
            return month
        return normalize_month(month)

    def set_month(self, month: Optional[str]) -> None:
        if month is not None:
            month = normalize_month(month)
            if month != "":
                self._entry[FieldNames.MONTH] = month
                return None
        if FieldNames.MONTH in self._entry:
            del self._entry[FieldNames.MONTH]
