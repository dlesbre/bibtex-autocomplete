"""
Abstract base classes used to represent queries

LookupProtocol(Protocol): duck-typing of lookups. They must have
  - an attribute name : str (UNIQUE)
  - a method query(self) -> Optional[BibtexEntry]
  - a method __init__(self, entry: Entry)
  - a method get_last_query_info(self) -> Dict[str, JSONType]
        with return extra information to add to data-dumps


AbstractLookup(): abstract base class, defines abstract methods

AbstractEntryLookup(AbstractLookup): entry attribute and __init__

AbstractDataLookup(AbstractLookup): split query into two new methods:
  - get_data : Self -> Data - to perform the actual query
  - process_data : Self, Data -> BibtexEntry - process data into a bibtex entry
"""

from typing import ClassVar, Dict, Generic, NamedTuple, Optional, Protocol, TypeVar

from ..utils.safe_json import JSONType

Input = TypeVar("Input", covariant=True)
Output = TypeVar("Output", covariant=True)


class LookupProtocol(Protocol, Generic[Input, Output]):
    """Minimal lookup, as used by the rest of the program,
    The generic "Input" and "Output" types are often "BibtexEntry",
    with exception for the URL and DOI validator lookups"""

    name: ClassVar[str]  # used to identify the lookup, also appears in help string

    def query(self) -> Optional[Output]:
        """Performs one or more queries to try and obtain the result
        VIRTUAL METHOD : must be overridden"""
        raise NotImplementedError("should be overridden in child class")

    def get_last_query_info(self) -> Dict[str, JSONType]:
        """Extra information to add to the data-dump about this query"""
        return dict()

    def __init__(self, input: Input) -> None:
        pass


class AbstractLookup(Generic[Input, Output]):
    """Abstract base class for lookup
    Is a valid LookupProtocol, but all methods should be overridden

    Use this as a base class for mixin so that super().query calls can typecheck"""

    name: ClassVar[str]  # used to identify the lookup, also appears in help string

    def query(self) -> Optional[Output]:
        """Performs one or more queries to try and obtain the result
        VIRTUAL METHOD : must be overridden"""
        raise NotImplementedError("should be overridden in child class")

    def get_last_query_info(self) -> Dict[str, JSONType]:
        """Extra information to add to the data-dump about this query"""
        return dict()

    def __init__(self, input: Input) -> None:
        pass


class Data(NamedTuple):
    data: bytes
    code: int
    reason: str
    delay: float


class AbstractDataLookup(AbstractLookup[Input, Output]):
    def get_data(self) -> Optional[Data]:
        """Performs a query to get data from the server
        VIRTUAL METHOD : must be overridden"""
        raise NotImplementedError("should be overridden in child class")

    def process_data(self, data: Data) -> Optional[Output]:
        """Should create a new entry with info extracted from data
        VIRTUAL METHOD : must be overridden"""
        raise NotImplementedError("should be overridden in child class")

    def query(self) -> Optional[Output]:
        """Tries to complete an entry
        override this to make multiple requests
        (i.e. try different search terms)"""
        data = self.get_data()
        if data is not None:
            return self.process_data(data)
        return None


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
