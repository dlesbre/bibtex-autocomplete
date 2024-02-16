"""
This modules specializes the classes in AbstractBase to use BibtexEntry as data
type. It is separate to avoid circular imports
"""

from typing import Set, Type

from ..bibtex.constants import FieldType, SearchedFields
from ..bibtex.entry import BibtexEntry
from .abstract_base import AbstractLookup, ConditionMixin, LookupProtocol

LookupType = Type[LookupProtocol["BibtexEntry", "BibtexEntry"]]


class AbstractEntryLookup(AbstractLookup[BibtexEntry, BibtexEntry]):
    """Abstract minimal lookup,
    Implements simple __init__ putting the argument in self.entry

    Virtual methods and attributes : (must be overridden in children):
    - name : str
    - query: Self -> Optional[BibtexEntry]
    """

    entry: BibtexEntry

    def __init__(self, input: BibtexEntry) -> None:
        super().__init__(input)
        self.entry = input


class FieldConditionMixin(ConditionMixin["BibtexEntry", "BibtexEntry"], AbstractEntryLookup):
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
