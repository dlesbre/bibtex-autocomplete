from typing import Dict, Literal, Optional, Set, Tuple, cast


class FieldNames:
    """constants for bibtex field names"""

    ADDRESS: Literal["address"] = "address"
    ANNOTE: Literal["annote"] = "annote"
    AUTHOR: Literal["author"] = "author"
    BOOKTITLE: Literal["booktitle"] = "booktitle"
    CHAPTER: Literal["chapter"] = "chapter"
    DOI: Literal["doi"] = "doi"
    EDITION: Literal["edition"] = "edition"
    EDITOR: Literal["editor"] = "editor"
    HOWPUBLISHED: Literal["howpublished"] = "howpublished"
    INSTITUTION: Literal["institution"] = "institution"
    ISSN: Literal["issn"] = "issn"
    ISBN: Literal["isbn"] = "isbn"
    JOURNAL: Literal["journal"] = "journal"
    MONTH: Literal["month"] = "month"
    NOTE: Literal["note"] = "note"
    NUMBER: Literal["number"] = "number"
    ORGANIZATION: Literal["organization"] = "organization"
    PAGES: Literal["pages"] = "pages"
    PUBLISHER: Literal["publisher"] = "publisher"
    SCHOOL: Literal["school"] = "school"
    SERIES: Literal["series"] = "series"
    TITLE: Literal["title"] = "title"
    TYPE: Literal["type"] = "type"
    URL: Literal["url"] = "url"
    VOLUME: Literal["volume"] = "volume"
    YEAR: Literal["year"] = "year"


FieldType = Literal[
    "address",
    "annote",
    "author",
    "booktitle",
    "chapter",
    "doi",
    "edition",
    "editor",
    "howpublished",
    "institution",
    "issn",
    "isbn",
    "journal",
    "month",
    "note",
    "number",
    "organization",
    "pages",
    "publisher",
    "school",
    "series",
    "title",
    "type",
    "url",
    "volume",
    "year",
]


# Set of all fields
FieldNamesSet: Set[FieldType] = {
    cast(FieldType, value)
    for attr, value in vars(FieldNames).items()
    if isinstance(value, str) and "_" not in attr and attr.upper() == attr
}

# Fields actually searched for
SearchedFields = FieldNamesSet.copy()


# Matching score range for fields
FIELD_FULL_MATCH = 100
FIELD_NO_MATCH = 0

# Weighted scores for field matches (default is 1)
# Additionaly, the boolean indicated fields which are critical,
# i.e. fields whose mismatch implies entry mismatch
FIELD_MULTIPLIERS: Dict[FieldType, Tuple[int, bool]] = {
    FieldNames.DOI: (100, True),
    FieldNames.TITLE: (20, True),
    FieldNames.AUTHOR: (10, True),
    FieldNames.YEAR: (5, True),
}


# Matching score range for entries
ENTRY_CERTAIN_MATCH = FIELD_FULL_MATCH * len(FieldNamesSet)
ENTRY_NO_MATCH = 0  # Any score below is no match


def cast_field_name(field: str) -> Optional[FieldType]:
    """Checks the string is a valid field and converts its type"""
    if field in FieldNamesSet:
        return cast(FieldType, field)
    return None
