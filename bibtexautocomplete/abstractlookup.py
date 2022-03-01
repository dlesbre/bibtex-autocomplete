# This file contains the abstract classes used to wrap http queries
# Inheritance structure:
#
#                         ABaseLookup
#                         basic lookup
#                          |   |   |
#       --------------------   |   -------------------
#       |                      |                     |
# ASearchLookup          AAuthorTitleLookup      ADOITitleLookup
#  parses result as       Make multiple queries    mulitple queries
#  a list of candidates   author and/or title      doi and/or title
#       |                      |
# AJSONSearchLookup            |
#  same as above               |
#  assumes data is JSON        |
#       |                      |
#       ----------   -----------
#                |   |
#               ALookup

from http.client import HTTPSConnection, socket  # type: ignore
from json import JSONDecodeError, JSONDecoder
from typing import Any, Dict, Generic, Iterable, Optional, TypeVar
from urllib.parse import urlencode

from .bibtex import PLAIN_PREFIX, get_authors, has_field
from .defs import (
    CONNECTION_TIMEOUT,
    EMAIL,
    USER_AGENT,
    EntryType,
    ResultType,
    logger,
    str_similar,
)


class ABaseLookup:
    """Abstract class to wrap https queries:
    Initialized with the entry to query info about
    - lookup() -> Optional[ResultType]
        method that performs the queries
    - different attributes and methods can be overridden to specify values
        namely get_params() which specify parameters to add to the url.
        the entry attribute can be used to initialize those parameters
    - handle_output(data: bytes) -> Optional[ResultType]
        must be overridden to process the output
        it returns None if not found or the relevant info if found
        Note that it MUST NOT change self.entry, only return the new values
    - query() -> Optional[ResultType]
        performs a single query, can be overridden for multiple queries
    """

    name: str  # used to identify the lookup, also appears in help string

    domain: str
    host: Optional[str] = None  # specify when different to domain
    path: str = "/"
    request: str = "GET"
    default_headers: Dict[str, str] = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Email": EMAIL,
    }
    headers: Dict[str, str] = {}
    params: Dict[str, str] = {}

    entry: EntryType

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

    def lookup(self) -> Optional[ResultType]:
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
        return self.handle_output(data)

    def handle_output(self, data: bytes) -> Optional[ResultType]:
        """Should modify self.entry with data extracted from data here"""
        raise NotImplementedError("should be overridden in child class")

    def query(self) -> Optional[ResultType]:
        """Tries to complete an entry
        override this to make multiple requests
        (i.e. try different search terms)"""
        return self.lookup()

    def __init__(self, entry: EntryType) -> None:
        self.entry = entry

    def get_entry_field(self, field: str) -> Optional[str]:
        """Safe access to self.entry's fields"""
        if has_field(self.entry, field):
            plain = PLAIN_PREFIX + field
            if plain in self.entry:
                return self.entry[plain].strip()
            return self.entry[field].strip()
        return None


class AAuthorTitleLookup(ABaseLookup):
    """Attempts multiple lookups, stop at first success:
    Attempts lookups using in order:
    - All authors (last name) + title
    - One author (last name) + title (for all authors, alphabetically)
    - title

    This DOES NOT create smart queries, it just updates self.author and self.title
    before each call to lookup(). Use these attributes in the relevant functions
    to build the correct query (i.e. in get_params)
    """

    author_join: str = " "
    author: Optional[str]
    title: Optional[str]

    # Politeness: avoid making too many queries when lots of authors
    max_search_queries: int = 10

    def query(self) -> Optional[ResultType]:
        self.title = self.get_entry_field("title")
        self.author = None
        if self.title is None:
            # No title, we can't compare entries
            return None
        if has_field(self.entry, "author"):
            authors = get_authors(self.entry[PLAIN_PREFIX + "author"])
            self.author = self.author_join.join(author.lastname for author in authors)
        if self.title is None and self.author is None:
            # No query data available
            return None

        # Query all authors + title
        lookup = self.lookup()
        if lookup is not None:
            return lookup

        # Query one authors + title
        if len(authors) > 1:
            queries = 1
            for author in authors:
                self.author = author.lastname
                lookup = self.lookup()
                if lookup is not None:
                    return lookup
                queries += 1
                if queries > self.max_search_queries:
                    break

        # Query title
        self.author = None
        if self.title is not None:
            lookup = self.lookup()
            return lookup
        return None


class ADOITitleLookup(ABaseLookup):
    """Attempts multiple lookups, stop at first success:
    Attempts lookups using in order:
    - DOI + title
    - title

    This DOES NOT create smart queries, it just updates self.doi and self.title
    before each call to lookup(). Use these attributes in the relevant functions
    to build the correct query (i.e. in get_params)
    """

    doi: Optional[str]
    title: Optional[str]

    def query(self) -> Optional[ResultType]:
        """Special query system
        if DOI is known, query with doi
        if fails or no doi, query with title"""
        self.title = self.get_entry_field("title")
        self.doi = self.get_entry_field("doi")
        if self.doi is not None:
            lookup = self.lookup()
            if lookup is not None:
                return lookup
            self.doi = None
        if self.title is not None:
            return self.lookup()
        return None


result = TypeVar("result")


class ASearchLookup(Generic[result], ABaseLookup):
    """Searches through lookup results
    provides and implementation of handle_output() using the following
    methods to override:
    - get_results(data: bytes) -> Optional[Iterable[result]]
        process data into a list of results
    - get_title(res: result) -> Optional[str]
        return a result's title, used to compare to entry
    - get_value(res: result) -> Optional[ResultType]
        return the found value
    """

    def get_results(self, data: bytes) -> Optional[Iterable[result]]:
        """Parse the data into a list of results to check
        Return None if no results/invalid data"""
        raise NotImplementedError("should be overridden in child class")

    def get_title(self, res: result) -> Optional[str]:
        """Returns a result's title, used to compare to reference entry"""
        raise NotImplementedError("should be overridden in child class")

    def get_value(self, res: result) -> ResultType:
        """Return the relevant value (e.g. DOI or URL)"""
        raise NotImplementedError("should be overridden in child class")

    def matches_entry(self, res: result) -> bool:
        """Return true if the result matches self.entry
        By default matches titles, can be overridden for different behavior"""
        res_title = self.get_title(res)
        entry_title = self.get_entry_field("title")
        return (
            (res_title is not None)
            and (entry_title is not None)
            and str_similar(res_title, entry_title)
        )

    def handle_output(self, data: bytes) -> Optional[ResultType]:
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


class AJSONSearchLookup(ASearchLookup[result]):
    """
    Version of ASearchLookup for JSON outputs
    replaces get_results(data: bytes) -> results
    with get_results_json(data: JSON)
    """

    def get_results(self, data: bytes) -> Optional[Iterable[result]]:
        try:
            data = JSONDecoder().decode(data.decode())
        except JSONDecodeError:
            return None
        return self.get_results_json(data)

    def get_results_json(self, data):
        raise NotImplementedError("should be overridden in child class")


class ALookup(AAuthorTitleLookup, AJSONSearchLookup[Dict[str, Any]]):
    """Shortand for common inheritance"""

    pass


LookupType = type[ABaseLookup]
