"""
Combine all the mixins into full fledge classes
"""

from ..utils.safe_json import SafeJSON
from .condition_mixin import FieldConditionMixin
from .https import HTTPSLookup
from .multiple_mixin import DATQueryMixin, DTQueryMixin, TitleAuthorQueryMixin
from .search_mixin import EntryMatchSearchMixin


class JSON_DAT_Lookup(
    FieldConditionMixin, DATQueryMixin, EntryMatchSearchMixin[SafeJSON], HTTPSLookup
):
    pass


class JSON_DT_Lookup(
    FieldConditionMixin, DTQueryMixin, EntryMatchSearchMixin[SafeJSON], HTTPSLookup
):
    pass


class JSON_AT_Lookup(
    FieldConditionMixin,
    TitleAuthorQueryMixin,
    EntryMatchSearchMixin[SafeJSON],
    HTTPSLookup,
):
    pass
