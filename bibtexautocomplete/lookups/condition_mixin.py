"""
Mixin to check if a condition holds before performing queries
"""

from typing import Optional

from ..bibtex.entry import BibtexEntry, SearchedFields
from .abstract_base import AbstractEntryLookup, AbstractLookup


class ConditionMixin(AbstractLookup):
    """Mixin to query only if a condition holds,

    inherit from this before the base Lookup class
    e.g. class MyLookup(..., ConditionMixin, ..., MyLookup):

    Adds the condition : Self -> bool method (default always True)"""

    def condition(self) -> bool:
        """override this to check a condition before
        performing any queries"""
        return True

    def query(self) -> Optional[BibtexEntry]:
        """calls parent query only if condition is met"""
        if self.condition():
            return super().query()
        return None


class FieldConditionMixin(ConditionMixin, AbstractEntryLookup):
    """Mixin used to query only if there exists a field in self.fields
    that does not exists in self.entry

    inherit from this before the base class
    e.g. class MyLookup(..., FieldConditionMixin, ..., MyLookup):

    Virtual attribute:
    - fields : Iterable[str] - list of fields that can be added to an entry by this lookup
    """

    # list of fields that can be added to an entry by this lookup
    fields: set[str]

    fields_to_complete: set[str] = SearchedFields

    def condition(self):
        """Only return True if there exists a field in self.fields
        that is not in self.entry"""
        for field in self.fields.intersection(self.fields_to_complete):
            if field not in self.entry:
                return True
        return False
