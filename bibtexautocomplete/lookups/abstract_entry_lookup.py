"""
This modules specializes the classes in AbstractBase to use BibtexEntry as data
type. It is separate to avoid circular imports
"""

from typing import Set, Type

from ..bibtex.constants import FieldType
from ..bibtex.entry import BibtexEntry
from .abstract_base import AbstractLookup


class AbstractEntryLookup(AbstractLookup[BibtexEntry, BibtexEntry]):
    """Abstract minimal lookup,
    Implements simple __init__ putting the argument in self.entry

    Virtual methods and attributes : (must be overridden in children):
    - name : str
    - query: Self -> Optional[BibtexEntry]
    """

    entry: BibtexEntry
    fields: Set[FieldType]

    def __init__(self, input: BibtexEntry) -> None:
        super().__init__(input)
        self.entry = input


LookupType = Type[AbstractEntryLookup]
