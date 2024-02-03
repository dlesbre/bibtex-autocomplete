"""
Mixin to check if a condition holds before performing queries
"""

from typing import TYPE_CHECKING, Optional, Set

from ..bibtex.constants import FieldType, SearchedFields
from .abstract_base import AbstractEntryLookup, AbstractLookup, Input, Output

if TYPE_CHECKING:
    from ..bibtex.entry import BibtexEntry  # noqa:F401


class ConditionMixin(AbstractLookup[Input, Output]):
    """Mixin to query only if a condition holds,

    inherit from this before the base Lookup class
    e.g. class MyLookup(..., ConditionMixin, ..., MyLookup):

    Adds the condition : Self -> bool method (default always True)"""

    def condition(self) -> bool:
        """override this to check a condition before
        performing any queries"""
        return True

    def query(self) -> Optional[Output]:
        """calls parent query only if condition is met"""
        if self.condition():
            return super().query()
        return None


class FieldConditionMixin(
    ConditionMixin["BibtexEntry", "BibtexEntry"], AbstractEntryLookup
):
    """Mixin used to query only if there exists a field in self.fields
    that does not exists in self.entry, or is in self.overwrites

    inherit from this before the base class
    e.g. class MyLookup(..., FieldConditionMixin, ..., MyLookup):

    Virtual attribute:
    - fields : Iterable[str] - list of fields that can be added to an entry by this lookup
    """

    # list of fields that can be added to an entry by this lookup
    fields: Set[FieldType]

    overwrites: Set[FieldType] = set()
    fields_to_complete: Set[FieldType] = SearchedFields

    def condition(self) -> bool:
        """Only return True if there exists a field in self.fields
        that is not in self.entry or that is in overwrites"""
        for field in self.fields.intersection(self.fields_to_complete):
            if field not in self.entry or field in self.overwrites:
                return True
        return False
