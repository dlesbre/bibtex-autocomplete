from typing import Literal, Optional, Set, cast


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

# Set of fields with sanitized inputs
SpecialFields: Set[FieldType] = {
    "author",
    "doi",
    "editor",
    "month",
}


def cast_field_name(field: str) -> Optional[FieldType]:
    """Checks the string is a valid field and converts its type"""
    if field in FieldNamesSet:
        return cast(FieldType, field)
    return None
