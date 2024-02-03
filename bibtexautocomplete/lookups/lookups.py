"""
Combine all the mixins into full fledge classes
"""

from xml.etree.ElementTree import Element

from ..bibtex.entry import BibtexEntry
from ..utils.safe_json import SafeJSON
from .abstract_entry_lookup import FieldConditionMixin
from .https import HTTPSRateCapedLookup
from .multiple_mixin import (
    DATQueryMixin,
    DTQueryMixin,
    TitleAuthorQueryMixin,
    TitleQueryMixin,
)
from .search_mixin import EntryMatchSearchMixin


class JSON_DAT_Lookup(
    FieldConditionMixin,
    DATQueryMixin,
    EntryMatchSearchMixin[SafeJSON],
    HTTPSRateCapedLookup[BibtexEntry, BibtexEntry],
):
    pass


class JSON_DT_Lookup(
    FieldConditionMixin,
    DTQueryMixin,
    EntryMatchSearchMixin[SafeJSON],
    HTTPSRateCapedLookup[BibtexEntry, BibtexEntry],
):
    pass


class JSON_AT_Lookup(
    FieldConditionMixin,
    TitleAuthorQueryMixin,
    EntryMatchSearchMixin[SafeJSON],
    HTTPSRateCapedLookup[BibtexEntry, BibtexEntry],
):
    pass


class XML_T_Lookup(
    FieldConditionMixin,
    TitleQueryMixin,
    EntryMatchSearchMixin[Element],
    HTTPSRateCapedLookup[BibtexEntry, BibtexEntry],
):
    pass
