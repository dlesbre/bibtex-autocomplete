"""
Combine all the mixins into full fledge classes
"""

from ..utils.safe_json import SafeJSON
from .condition_mixin import FieldConditionMixin
from .https import HTTPSRateCapedLookup
from .multiple_mixin import DATQueryMixin, DTQueryMixin, TitleAuthorQueryMixin
from .search_mixin import EntryMatchSearchMixin


class JSON_DAT_Lookup(
    FieldConditionMixin,
    DATQueryMixin,
    EntryMatchSearchMixin[SafeJSON],
    HTTPSRateCapedLookup,
):
    pass


class JSON_DT_Lookup(
    FieldConditionMixin,
    DTQueryMixin,
    EntryMatchSearchMixin[SafeJSON],
    HTTPSRateCapedLookup,
):
    pass


class JSON_AT_Lookup(
    FieldConditionMixin,
    TitleAuthorQueryMixin,
    EntryMatchSearchMixin[SafeJSON],
    HTTPSRateCapedLookup,
):
    pass
