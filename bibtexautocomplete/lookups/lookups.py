"""
Combine all the mixins into full fledge classes
"""

from xml.etree.ElementTree import Element

from ..bibtex.entry import BibtexEntry
from ..utils.safe_json import SafeJSON
from .abstract_entry_lookup import FieldConditionMixin
from .https import HTTPSRateCapedLookup
from .multiple_mixin import DAT_Query_Mixin
from .search_mixin import EntryMatchSearchMixin


class JSON_Lookup(
    FieldConditionMixin,
    DAT_Query_Mixin,
    EntryMatchSearchMixin[SafeJSON],
    HTTPSRateCapedLookup[BibtexEntry, BibtexEntry],
):
    pass


class XML_Lookup(
    FieldConditionMixin,
    DAT_Query_Mixin,
    EntryMatchSearchMixin[Element],
    HTTPSRateCapedLookup[BibtexEntry, BibtexEntry],
):
    pass
