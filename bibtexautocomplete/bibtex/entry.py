"""
Wraps around bibtexparser's entry representations for safer access
and field normalization
"""

from typing import Any, Iterator, List, Optional, Tuple, cast

from ..utils.constants import EntryType
from .author import Author
from .base_field import BibtexField
from .constants import (
    FieldNames,
    FieldNamesSet,
    FieldType,
    SpecialFields,
    cast_field_name,
)
from .fields import (
    AbbreviatedStringField,
    BasicStringField,
    DOIField,
    ISBNField,
    ISSNField,
    MonthField,
    NameField,
    PagesField,
    URLField,
    YearField,
)
from .normalize import (
    get_field,
    has_data,
    has_field,
    normalize_doi,
    normalize_month,
    normalize_year,
)


class BibtexEntry2:
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

    address: BibtexField[str]
    annote: BibtexField[str]
    author: NameField  # BibtexField[List[Author]]
    booktitle: BibtexField[str]
    chapter: BibtexField[str]
    doi: DOIField  # BibtexField[str]
    edition: BibtexField[str]
    editor: NameField  # BibtexField[List[Author]]
    howpublished: BibtexField[str]
    institution: BibtexField[str]
    issn: ISSNField  # BibtexField[List[str]]
    isbn: ISBNField  # BibtexField[str]
    journal: BibtexField[str]
    month: MonthField  # BibtexField[str]
    note: BibtexField[str]
    number: BibtexField[str]
    organization: BibtexField[str]
    pages: PagesField  # BibtexField[List[str]]
    publisher: BibtexField[str]
    school: BibtexField[str]
    series: BibtexField[str]
    title: BibtexField[str]
    type: BibtexField[str]
    url: BibtexField[str]
    volume: BibtexField[str]
    year: YearField  # BibtexField[str]

    def __init__(self, source: str):
        """Create a new empty entry,
        source identifies the data's provenance (i.e. lookup name, bibtex file...)"""
        self.address = BasicStringField("address", source)
        self.annote = BasicStringField("annote", source)
        self.author = NameField("author", source)
        self.booktitle = AbbreviatedStringField("booktitle", source)
        self.chapter = BasicStringField("chapter", source)
        self.doi = DOIField("doi", source)
        self.edition = BasicStringField("edition", source)
        self.editor = NameField("editor", source)
        self.howpublished = BasicStringField("howpublished", source)
        self.institution = AbbreviatedStringField("institution", source)
        self.issn = ISSNField("issn", source)
        self.isbn = ISBNField("isbn", source)
        self.journal = AbbreviatedStringField("journal", source)
        self.month = MonthField("month", source)
        self.note = BasicStringField("note", source)
        self.number = BasicStringField("number", source)
        self.organization = AbbreviatedStringField("organization", source)
        self.pages = PagesField("pages", source)
        self.publisher = AbbreviatedStringField("publisher", source)
        self.school = AbbreviatedStringField("school", source)
        self.series = AbbreviatedStringField("series", source)
        self.title = BasicStringField("title", source)
        self.type = BasicStringField("type", source)
        self.url = URLField("url", source)
        self.volume = BasicStringField("volume", source)
        self.year = YearField("year", source)

    def get_field(self, field: FieldType) -> BibtexField[Any]:
        return cast(BibtexField[Any], self.__getattribute__(field))

    def from_entry(self, entry: EntryType) -> None:
        """Initialize self from a bibtexparser entry"""
        for field in entry:
            cfield = cast_field_name(field)
            if cfield is not None:
                self.get_field(cfield).set_str(entry[field])


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

    _entry: EntryType

    def __init__(self, entry: Optional[EntryType] = None):
        """Init is not thread safe"""
        if entry is None:
            self._entry = dict()
        else:
            self._entry = entry.copy()

    def __getattribute__(self, attr_name: str) -> Any:
        """Performs checks when returning Bibtex fields"""
        if attr_name in FieldNamesSet:
            if attr_name in SpecialFields:
                return super().__getattribute__("get_" + attr_name)()
            return get_field(self._entry, attr_name)
        return super().__getattribute__(attr_name)

    def __setattr__(self, attr_name: str, value: Any) -> None:
        """Performs checks when returning Bibtex fields"""
        if attr_name in FieldNamesSet:
            if attr_name in SpecialFields:
                super().__getattribute__("set_" + attr_name)(value)
                return None
            elif not has_data(value):
                # Delete attribute
                if attr_name in self._entry:
                    del self._entry[attr_name]
            else:
                self._entry[attr_name] = value
            return None
        super().__setattr__(attr_name, value)

    def __delattr__(self, attr_name: str) -> None:
        if attr_name in FieldNamesSet:
            if attr_name in self._entry:
                del self._entry[attr_name]
            return
        return super().__delattr__(attr_name)

    def __contains__(self, field: str) -> bool:
        """Is the given field non empty in this entry?"""
        return field in FieldNamesSet and has_field(self._entry, field)

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        """Iterates through the fields of self"""
        return filter(
            lambda pair: pair[0] in FieldNamesSet and has_data(pair[1]),
            self._entry.items(),
        )

    def get_author(self) -> List[Author]:
        """Formats entry['author'] into Author list"""
        authors = get_field(self._entry, FieldNames.AUTHOR)
        if authors is not None:
            return Author.from_namelist(authors)
        return []

    def get_editor(self) -> List[Author]:
        """Formats entry['editor'] into Author list"""
        authors = get_field(self._entry, FieldNames.EDITOR)
        if authors is not None:
            return Author.from_namelist(authors)
        return []

    def set_author(self, authors: List[Author]) -> None:
        """set entry['author']"""
        if len(authors) == 0:
            if FieldNames.AUTHOR in self._entry:
                del self._entry[FieldNames.AUTHOR]
        else:
            self._entry[FieldNames.AUTHOR] = Author.list_to_bibtex(authors)

    def set_editor(self, authors: List[Author]) -> None:
        """set entry['editor']"""
        if len(authors) == 0:
            if FieldNames.EDITOR in self._entry:
                del self._entry[FieldNames.EDITOR]
        else:
            self._entry[FieldNames.EDITOR] = Author.list_to_bibtex(authors)

    def get_doi(self) -> Optional[str]:
        """get the doi without leading url"""
        return normalize_doi(get_field(self._entry, FieldNames.DOI))

    def set_doi(self, doi: str) -> None:
        """get the doi without leading url"""
        value = normalize_doi(doi)
        if value is None:
            if FieldNames.DOI in self._entry:
                del self._entry[FieldNames.DOI]
        else:
            self._entry[FieldNames.DOI] = value

    def get_month(self) -> Optional[str]:
        month = get_field(self._entry, FieldNames.MONTH)
        if month is None:
            return None
        return normalize_month(month)

    def set_month(self, month: Optional[str]) -> None:
        if month is not None:
            month = normalize_month(month)
            if month != "" and month is not None:
                self._entry[FieldNames.MONTH] = month
                return None
        if FieldNames.MONTH in self._entry:
            del self._entry[FieldNames.MONTH]

    def get_year(self) -> Optional[str]:
        year = get_field(self._entry, FieldNames.YEAR)
        if year is None:
            return None
        n = normalize_year(year)
        if n is None:
            return year
        return str(n)

    def set_year(self, year: Optional[str]) -> None:
        if year is not None:
            n = normalize_year(year)
            year = year if n is None else str(n)
            self._entry[FieldNames.YEAR] = year
            return None
        if FieldNames.YEAR in self._entry:
            del self._entry[FieldNames.YEAR]
