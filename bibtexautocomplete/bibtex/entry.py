"""
Wraps around bibtexparser's entry representations for safer access
and field normalization
"""

from typing import Any, Dict, Set, cast

from ..utils.constants import EntryType
from .base_field import BibtexField
from .constants import (
    ENTRY_NO_MATCH,
    FIELD_MULTIPLIERS,
    FIELD_NO_MATCH,
    FieldNamesSet,
    FieldType,
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

    id: str

    def __init__(self, source: str, entry_id: str):
        """Create a new empty entry,
        source identifies the data's provenance (i.e. lookup name, bibtex file...)
        entry_id is the identifier used to for the entry (@article{entry_id, ...})"""
        self.id = entry_id
        self.address = BasicStringField("address", source, entry_id)
        self.annote = BasicStringField("annote", source, entry_id)
        self.author = NameField("author", source, entry_id)
        self.booktitle = AbbreviatedStringField("booktitle", source, entry_id)
        self.chapter = BasicStringField("chapter", source, entry_id)
        self.doi = DOIField("doi", source, entry_id)
        self.edition = BasicStringField("edition", source, entry_id)
        self.editor = NameField("editor", source, entry_id)
        self.howpublished = BasicStringField("howpublished", source, entry_id)
        self.institution = AbbreviatedStringField("institution", source, entry_id)
        self.issn = ISSNField("issn", source, entry_id)
        self.isbn = ISBNField("isbn", source, entry_id)
        self.journal = AbbreviatedStringField("journal", source, entry_id)
        self.month = MonthField("month", source, entry_id)
        self.note = BasicStringField("note", source, entry_id)
        self.number = BasicStringField("number", source, entry_id)
        self.organization = AbbreviatedStringField("organization", source, entry_id)
        self.pages = PagesField("pages", source, entry_id)
        self.publisher = AbbreviatedStringField("publisher", source, entry_id)
        self.school = AbbreviatedStringField("school", source, entry_id)
        self.series = AbbreviatedStringField("series", source, entry_id)
        self.title = BasicStringField("title", source, entry_id)
        self.type = BasicStringField("type", source, entry_id)
        self.url = URLField("url", source, entry_id)
        self.volume = BasicStringField("volume", source, entry_id)
        self.year = YearField("year", source, entry_id)

    def get_field(self, field: FieldType) -> BibtexField[Any]:
        return cast(BibtexField[Any], self.__getattribute__(field))

    @staticmethod
    def from_entry(source: str, entry: EntryType) -> "BibtexEntry":
        """Initialize self from a bibtexparser entry"""
        entry_id = entry.get("ID", "unnamed")
        bib_entry = BibtexEntry(source, entry_id)
        for field in entry:
            cfield = cast_field_name(field)
            if cfield is not None:
                bib_entry.get_field(cfield).set_str(entry[field])
        return bib_entry

    def matches(self, other: "BibtexEntry") -> int:
        """Computes a match score with the other entry
        A score of ENTRY_NO_MATCH indicates a mismatch
        Higher scores indicate more likely match"""
        total = ENTRY_NO_MATCH
        # Match title
        title_match = self.get_field("title").matches(other.get_field("title"))
        if title_match is not None:
            total += FIELD_MULTIPLIERS["title"][0] * title_match
        # Match DOI
        doi_match = self.get_field("doi").matches(other.get_field("doi"))
        if doi_match is not None:
            total += FIELD_MULTIPLIERS["doi"][0] * doi_match
        # If neither title nor DOI match, we can't id the entry with any certainty
        if total <= ENTRY_NO_MATCH:
            return ENTRY_NO_MATCH
        # match all other fields
        for field in FieldNamesSet - {"title", "doi"}:
            score = self.get_field(field).matches(other.get_field(field))
            if score is not None:
                if field in FIELD_MULTIPLIERS:
                    mult, critical = FIELD_MULTIPLIERS[field]
                    if score <= FIELD_NO_MATCH and critical:
                        return ENTRY_NO_MATCH
                    score *= mult
                total += score
        return total

    def __contains__(self, field: FieldType) -> bool:
        """Check if the given field has a value"""
        return self.get_field(field).value is not None

    def __str__(self) -> str:
        fields: Dict[FieldType, str] = dict()
        for field in FieldNamesSet:
            fd = self.get_field(field)
            if fd.value is not None:
                fields[field] = fd.value
        return f"Entry{fields}"

    def fields(self) -> Set[FieldType]:
        """Set of fields with valid values"""
        return {x for x in FieldNamesSet if x in self}
