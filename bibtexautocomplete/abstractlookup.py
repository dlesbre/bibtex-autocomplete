"""This file contains the abstract classes used to wrap http queries

Lookups ==================================

LookupProtocol(Protocol): duck-typing of lookups. They must have
  - an attribute name : str
  - a method query(self) -> Optional[BibtexEntry]
  - a method __init__(self, entry: Entry)

ABCLookup(): abstract base class, defines abstract methods
AMinimalLookup(ABCLookup): entry attribute and __init__
ABaseLookup(AMinimalLookup): single https query using
  attributes domain, headers, params... and matching methods
  abstract handle_output method to process output

JSONLookup(FieldConditionMixin, DATQueryMixin, DOITitleSearchMixin[SafeJSON], ABaseLookup):

Mixins ==================================

ConditionMixin(ABCLookup): query only if self.condition() holds
FieldConditionMixin(ConditionMixin, AMinimalLookup):
  query only if some fields in self.fields are not defined in self.entry

MultipleQueryMixin(ABCLookup): perform multiple queries (using self.iter_queries)
  stop at first valid result
DOIQueryMixin(MultipleQueryMixin, AMinimalLookup):
  if entry has doi, set self.doi, query, unset, call parent queries
TitleQueryMixin(MultipleQueryMixin, AMinimalLookup):
  if entry has title, set self.title, call parent queries, query, unset
AuthorQueryMixin(MultipleQueryMixin, AMinimalLookup):
  if entry has authors, set self.authors (to all last names),
  call parent queries, query, query for each author individually, unset
DATQueryMixin(TitleQueryMixin, AuthorQueryMixin, DOIQueryMixin):
  queries in order:
  - if doi, with doi, with title (if any), with all authors (if any)
  - if authors, with all authors, with title (if any)
  - if authors, with each author individually, with title (if any)
  - if title, with title (if any)

SearchResultMixin(Generic[T]): when returned data contains a list of candidates,
  search through them until one matches
DOITitleSearchMixin(SearchResultMixin[T], AMinimalLookup):
  matches based on doi (if present on both) or title (with str_similar)
"""

from http.client import HTTPSConnection, socket  # type: ignore
from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    Iterator,
    Optional,
    Protocol,
    Type,
    TypeVar,
)
from urllib.parse import urlencode

from .bibtex import BibtexEntry
from .defs import (
    CONNECTION_TIMEOUT,
    EMAIL,
    USER_AGENT,
    SafeJSON,
    extract_doi,
    logger,
    str_similar,
)

# =================================================
# § Lookups
# =================================================


class LookupProtocol(Protocol):
    name: str  # used to identify the lookup, also appears in help string

    def query(self) -> Optional[BibtexEntry]:
        """Performs one or more queries to try and obtain the result
        VIRTUAL METHOD : must be overridden"""
        raise NotImplementedError("should be overridden in child class")

    def __init__(self, entry: BibtexEntry) -> None:
        pass


LookupType = Type[LookupProtocol]


class ABCLookup:
    name: str  # used to identify the lookup, also appears in help string

    def query(self) -> Optional[BibtexEntry]:
        """Performs one or more queries to try and obtain the result
        VIRTUAL METHOD : must be overridden"""
        raise NotImplementedError("should be overridden in child class")

    def __init__(self, entry: BibtexEntry) -> None:
        super().__init__()


class AMinimalLookup(ABCLookup):
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


class ABaseLookup(AMinimalLookup):
    """Abstract class to wrap https queries:
    Initialized with the entry to query info about

    Defines:
    - lookup : Self -> Optional[bytes] - performs the queries and returns raw data
    - query : Self -> Optional[BibtexEntry] - performs single query, calls lookup and handle_output

    - domain: str = "localhost" - the domain name e.g. api.crossref.org
    - host : Optional[str] = None - host when different from domain
    - path : str = "/" - the path component of the URL
    - params : Dict[str, str] = {} - parameters to add to the URL

    - request : str = "GET" - https request type
    - default_headers : Dict[str, str] = ... default http header
    - headers : Dict[str, str] = {} - headers to add, overrite default_headers

    all of these have associated methods get_XX : Self -> Type[XX] that can be overridden
    for finer behavior control

    Virtual methods and attributes:
    - handle_output : Self, bytes -> Optional[Result] - parses output into useful result
    """

    domain: str = "localhost"
    host: Optional[str] = None
    path: str = "/"
    params: Dict[str, str] = {}

    request: str = "GET"
    default_headers: Dict[str, str] = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Email": EMAIL,
    }
    headers: Dict[str, str] = {}

    connection_timeout: float = CONNECTION_TIMEOUT

    def get_headers(self) -> Dict[str, str]:
        """Return the headers used in an HTTPS request"""
        headers = self.default_headers.copy()
        headers.update(self.headers)
        headers["Host"] = self.get_host()
        return headers

    def get_request(self) -> str:
        """Return the request method to use
        override this if not using self.request (default GET)"""
        return self.request

    def get_domain(self) -> str:
        """Return the path to connect to
        override this if not using self.domain"""
        return self.domain

    def get_host(self) -> str:
        """Return the host header
        override this if not using self.host or self.domain"""
        if self.host is not None:
            return self.host
        return self.get_domain()

    def get_path(self) -> str:
        """Return the path to connect to
        override this if not using self.path"""
        params = self.get_params()
        if params:
            return self.path + "?" + urlencode(params)
        return self.path

    def get_params(self) -> Dict[str, str]:
        """Url parameters, can use self.entry to set them
        override this if not using self.path"""
        return self.params

    def get_body(self) -> Optional[Any]:
        """Query body, can use self.entry to set them"""
        return None

    def lookup(self) -> Optional[bytes]:
        """main lookup function
        returns true if the lookup succeeded in finding all info
        false otherwise"""
        domain = self.get_domain()
        request = self.get_request()
        path = self.get_path()
        headers = self.get_headers()
        logger.info(f"{request} {domain} {path}")
        # logger.debug(f"{headers}")
        try:
            connection = HTTPSConnection(domain, timeout=self.connection_timeout)
            connection.request(
                request,
                path,
                self.get_body(),
                headers,
            )
            response = connection.getresponse()
            logger.info(f"response: {response.status} {response.reason}")
            if response.status != 200:
                connection.close()
                return None
            data = response.read()
            connection.close()
        except socket.timeout:
            logger.warn("connection timeout")
            return None
        except socket.gaierror as err:
            logger.warn(f"connection error: {err}")
            return None
        return data

    def handle_output(self, data: bytes) -> Optional[BibtexEntry]:
        """Should create a new entry with info extracted from data
        Should NOT modify self.entry
        VIRTUAL METHOD : must be overridden"""
        raise NotImplementedError("should be overridden in child class")

    def query(self) -> Optional[BibtexEntry]:
        """Tries to complete an entry
        override this to make multiple requests
        (i.e. try different search terms)"""
        data = self.lookup()
        if data is not None:
            return self.handle_output(data)
        return None


# =================================================
# § ConditionMixin
# =================================================


class ConditionMixin(ABCLookup):
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


class FieldConditionMixin(ConditionMixin, AMinimalLookup):
    """Mixin used to query only if there exists a field in self.fields
    that does not exists in self.entry

    inherit from this before the base class
    e.g. class MyLookup(..., FieldConditionMixin, ..., MyLookup):

    Virtual attribute:
    - fields : Iterable[str] - list of fields that can be added to an entry by this lookup
    """

    entry: BibtexEntry

    # list of fields that can be added to an entry by this lookup
    fields: Iterable[str]

    def condition(self):
        """Only return True if there exists a field in self.fields
        that is not in self.entry"""
        for field in self.fields:
            if field not in self.entry:
                return True
        return False


# =================================================
# § MultipleQueryMixin
# =================================================


class MultipleQueryMixin(ABCLookup):
    """Mixin to perform multiple queries

    Defines:
    - iter_queries : Self -> Iterator[None] - empty iterator (should be overridden)
    - query : Self -> Optional[BibtexEntry] - call parent query as long as iter_query yields
        stop a first valid (non None) value
    """

    def iter_queries(self) -> Iterator[None]:
        """Used to iterate through the queries
        The yielded result doesn't really matter.
        This method should dynamically modify attributes (like self.title)
        which are then used when constructing queries (i.e. in get_param())
        Default behavior: no queries"""
        return iter([])

    def query(self) -> Optional[BibtexEntry]:
        """Performs queries as long as iter_query yields
        Stops at first valid result found"""
        for _ in self.iter_queries():
            value = super().query()
            if value is not None:
                return value
        return None


class DOIQueryMixin(MultipleQueryMixin, AMinimalLookup):
    """Performs one query setting self.doi if self.entry has a doi
    then parent queries if any
    """

    doi: Optional[str] = None

    def iter_queries(self) -> Iterator[None]:
        self.doi = self.entry.doi
        if self.doi is not None:
            yield None
        # Perform more queries without doi
        self.doi = None
        for x in super().iter_queries():
            yield x


class TitleQueryMixin(MultipleQueryMixin, AMinimalLookup):
    """Sets self.title if self.entry has a title
    Performs parent queries if any
    then perform a single query if self.title is set
    """

    title: Optional[str] = None

    def iter_queries(self) -> Iterator[None]:
        self.title = self.entry.title
        # Perform parent queries with title set
        for x in super().iter_queries():
            yield x
        if self.title is not None:
            yield None


class AuthorQueryMixin(MultipleQueryMixin, AMinimalLookup):
    """
    Sets self.title to entry title if any
    Sets self.author if self.entry has a authors to space separated list of lastnames
    Performs parent queries if any
    if self.title:
      performs a single query if self.author is not None
      performs a query per author (resetting self.author to just one author) if more than one author
      unsets self.author
      performs a single query
    """

    entry: BibtexEntry
    author_join: str = " "
    title: Optional[str] = None
    author: Optional[str] = None

    def iter_queries(self) -> Iterator[None]:
        # Find and format authors
        self.title = self.entry.title
        authors = self.entry.author
        if authors:
            self.author = self.author_join.join(author.lastname for author in authors)
        # Perform parent queries
        for x in super().iter_queries():
            yield x
        if self.title is None:
            return None
        # Perform one query with all authors
        yield None
        if len(authors) == 1:
            return
        for author in authors:
            # Perform one query per author
            self.author = author.lastname
            yield None
        self.author = None
        yield None


class DATQueryMixin(TitleQueryMixin, AuthorQueryMixin, DOIQueryMixin):
    """DOI - Authors - Title Mixin
    queries in order:
    - if doi, with doi, with title (if any), with all authors (if any)
    - if authors, with all authors, with title (if any)
    - if authors, with each author individually, with title (if any)
    - if title, with title (if any)"""

    pass


# =================================================
# § SearchResultMixin
# =================================================


result = TypeVar("result")


class SearchResultMixin(Generic[result]):
    """Iterates through multiple results until a matching one is found

    Defines:
    - handle_output : bytes -> Optional[BibtexEntry]

    Virtual methods defined here:
    - get_results : bytes -> Optional[Iterable[result]]
        process data into a list of results
        return a result's title, used to compare to entry
    - matches_entry : result -> bool - does the result match self.entry ?
    - get_value : result -> Optional[BibtexEntry] - builds value from a matching result"""

    def get_results(self, data: bytes) -> Optional[Iterable[result]]:
        """Parse the data into a list of results to check
        Return None if no results/invalid data"""
        raise NotImplementedError("should be overridden in child class")

    def get_value(self, res: result) -> BibtexEntry:
        """Return the relevant value (e.g. updated entry)"""
        raise NotImplementedError("should be overridden in child class")

    def matches_entry(self, res: result) -> bool:
        """Return true if the result matches self.entry
        By default matches titles, can be overridden for different behavior"""
        raise NotImplementedError("should be overridden in child class")

    def handle_output(self, data: bytes) -> Optional[BibtexEntry]:
        results = self.get_results(data)
        if results is None:
            logger.debug("no results")
            return None
        for res in results:
            if self.matches_entry(res):
                # We found a match,
                # No need to keep searching or querying this database
                # even if the match is empty
                return self.get_value(res)
        return None


class DOITitleSearchMixin(SearchResultMixin[result], AMinimalLookup):
    """matches based on doi (if present on both) or title (with str_similar)

    Virtual methods:
    - get_doi : result -> Optional[str]
    - get_title : result -> Optional[str]"""

    def get_doi(self, res: result) -> Optional[str]:
        """Return the result's DOI if present"""
        raise NotImplementedError("should be overridden in child class")

    def get_title(self, res: result) -> Optional[str]:
        """Return the result's title if present"""
        raise NotImplementedError("should be overridden in child class")

    def matches_entry(self, res: result) -> bool:
        res_doi = extract_doi(self.get_doi(res))
        ent_doi = self.entry.doi
        if res_doi is not None and ent_doi is not None and res_doi == ent_doi:
            return True
        res_title = self.get_title(res)
        ent_title = self.entry.title
        return (
            res_title is not None
            and ent_title is not None
            and str_similar(ent_title, res_title)
        )


# =================================================
# §
# =================================================


class JSONLookup(
    FieldConditionMixin, DATQueryMixin, DOITitleSearchMixin[SafeJSON], ABaseLookup
):
    """Bringing all mixins together"""

    pass
