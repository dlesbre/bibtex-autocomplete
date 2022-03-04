"""
Abstract base classes used to represent queries

LookupProtocol(Protocol): duck-typing of lookups. They must have
  - an attribute name : str (UNIQUE)
  - a method query(self) -> Optional[BibtexEntry]
  - a method __init__(self, entry: Entry)


AbstractLookup(): abstract base class, defines abstract methods

AbstractEntryLookup(AbstractLookup): entry attribute and __init__

AbstractDataLookup(AbstractLookup): split query into two new methods:
  - get_data : Self -> bytes - to perform the actual query
  - process_data : Self, bytes -> BibtexEntry - process data into a bibtex entry
"""

from typing import Optional, Protocol

from ..bibtex.entry import BibtexEntry


class LookupProtocol(Protocol):
    name: str  # used to identify the lookup, also appears in help string

    def query(self) -> Optional[BibtexEntry]:
        """Performs one or more queries to try and obtain the result
        VIRTUAL METHOD : must be overridden"""
        raise NotImplementedError("should be overridden in child class")

    def __init__(self, entry: BibtexEntry) -> None:
        pass


LookupType = type[LookupProtocol]


class AbstractLookup:
    """Abstract base class for lookup
    Is a valid LookupProtocol, but all methods should be overridden

    Use this as a base class for mixin so that super().query calls can typecheck"""

    name: str  # used to identify the lookup, also appears in help string

    def query(self) -> Optional[BibtexEntry]:
        """Performs one or more queries to try and obtain the result
        VIRTUAL METHOD : must be overridden"""
        raise NotImplementedError("should be overridden in child class")

    def __init__(self, entry: BibtexEntry) -> None:
        super().__init__()


class AbstractEntryLookup(AbstractLookup):
    """Abstract minimal lookup,
    Implements simple __init__ putting the argument in self.entry

    Virtual methods and attributes : (must be overridden in children):
    - name : str
    - query: Self -> Optional[BibtexEntry]
    """

    entry: BibtexEntry

    def __init__(self, entry: BibtexEntry) -> None:
        super().__init__(entry)
        self.entry = entry


class AbstractDataLookup(AbstractLookup):
    def get_data(self) -> Optional[bytes]:
        """Performs a query to get data from the server
        VIRTUAL METHOD : must be overridden"""
        raise NotImplementedError("should be overridden in child class")

    def process_data(self, data: bytes) -> Optional[BibtexEntry]:
        """Should create a new entry with info extracted from data
        VIRTUAL METHOD : must be overridden"""
        raise NotImplementedError("should be overridden in child class")

    def query(self) -> Optional[BibtexEntry]:
        """Tries to complete an entry
        override this to make multiple requests
        (i.e. try different search terms)"""
        data = self.get_data()
        if data is not None:
            return self.process_data(data)
        return None
