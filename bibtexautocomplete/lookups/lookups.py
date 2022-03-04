"""
Combine all the mixins into full fledge classes
"""

from ..utils.safe_json import SafeJSON
from .condition_mixin import FieldConditionMixin
from .https import HTTPSLookup
from .multiple_mixin import DATQueryMixin, DTQueryMixin
from .search_mixin import DOITitleSearchMixin


class JSON_DAT_Lookup(
    FieldConditionMixin, DATQueryMixin, DOITitleSearchMixin[SafeJSON], HTTPSLookup
):
    pass


class JSON_DT_Lookup(
    FieldConditionMixin, DTQueryMixin, DOITitleSearchMixin[SafeJSON], HTTPSLookup
):
    pass
