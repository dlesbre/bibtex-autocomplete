from http.client import HTTPSConnection, socket  # type: ignore
from json import JSONDecodeError, JSONDecoder
from typing import Any, Dict, Generic, List, Optional, TypeVar
from urllib.parse import urlencode

from .bibtex import get_authors, has_field
from .constants import CONNECTION_TIMEOUT, USER_AGENT, EntryType, logger, str_similar


class Lookup:
    """Abstract class to wrap queries"""

    domain: str
    host: Optional[str] = None  # specify when different to domain
    path: str = "/"
    request: str = "GET"
    default_headers: Dict[str, str] = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    headers: Dict[str, str] = {}
    params: Dict[str, str] = {}

    entry: EntryType

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

    def lookup(self) -> Optional[str]:
        """main lookup function
        returns true if the lookup succeeded in finding all info
        false otherwise"""
        domain = self.get_domain()
        request = self.get_request()
        path = self.get_path()
        headers = self.get_headers()
        logger.info(f"{request} {domain} {path}")
        logger.debug(f"{headers}")
        try:
            connection = HTTPSConnection(domain, timeout=CONNECTION_TIMEOUT)
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

    def handle_output(self, data: bytes) -> Optional[str]:
        """Should modify self.entry with data extracted from data here"""
        raise NotImplementedError("should be overridden in child class")

    def complete(self) -> Optional[str]:
        """Tries to complete an entry
        override this to make multiple requests
        (i.e. try different search terms)"""
        return self.lookup()

    def __init__(self, entry: EntryType) -> None:
        self.entry = entry


class MultipleLookup(Lookup):
    """Attempts multiple lookups, stop at first success:
    Attempts lookups using in order:
    - All authors (last name) + title
    - One author (last name) + title (for all authors, alphabetically)
    - title

    This DOES NOT do any real work, just update self.author and self.title
    before each call to lookup(). Use these attributes in the relevant functions
    to build the correct query
    """

    author_join: str = " "
    author: Optional[str]
    title: Optional[str]

    # Politeness: avoid making too many queries when lots of authors
    max_search_queries: int = 10

    def complete(self) -> Optional[str]:
        if has_field(self.entry, "title"):
            self.title = self.entry["plain_title"].strip()
        if has_field(self.entry, "author"):
            authors = get_authors(self.entry["plain_author"])
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


result = TypeVar("result")


class SearchLookup(Generic[result], Lookup):
    """Searches through lookup results"""

    def get_results(self, data: bytes) -> Optional[List[result]]:
        """Parse the data into a list of results to check
        Return None if no results/invalid data"""
        raise NotImplementedError("should be overridden in child class")

    def get_title(self, res: result) -> Optional[str]:
        """Returns a result's title, used to compare to reference entry"""
        raise NotImplementedError("should be overridden in child class")

    def get_value(self, res: result) -> Optional[str]:
        """Return the relevant value (e.g. DOI or URL)
        This should also update self.entry with the value"""
        raise NotImplementedError("should be overridden in child class")

    def handle_output(self, data: bytes) -> Optional[str]:
        results = self.get_results(data)
        if results is None:
            return None
        for res in results:
            title = self.get_title(res)
            if title is None:
                continue
            value = self.get_value(res)
            if value is not None:
                return value
        return None


class JSONLookup(Lookup):
    def handle_output(self, data: bytes) -> Optional[str]:
        try:
            data = JSONDecoder().decode(data.decode())
        except JSONDecodeError:
            return None
        self.handle_json(data)
        return None

    def handle_json(self, data):
        raise NotImplementedError("should be overridden in child class")


class CrossrefLookup(MultipleLookup, SearchLookup[Dict[str, Any]]):
    """Lookup info on https://www.crossref.org
    Uses the crossref REST API, documentated here:
    https://api.crossref.org/swagger-ui/index.html
    """

    domain = "api.crossref.org"
    path = "/works"

    author: Optional[str]

    def get_params(self) -> Dict[str, str]:
        base = {"rows": "3", "query.title": self.entry["title"]}
        if self.author is not None:
            base["query.author"] = self.author
        return base

    def complete(self) -> Optional[str]:
        self.author = self.entry["author"]
        return self.lookup()

    def handle_output(self, data) -> Optional[str]:
        try:
            data = JSONDecoder().decode(data.decode())
        except JSONDecodeError:
            return None
        if data["status"] != "ok":
            return None
        items = data["message"]["items"]
        for item in items:
            if "title" in item and str_similar(item["title"][0], self.entry["title"]):
                if "DOI" in item:
                    doi = item["DOI"]
                    self.entry["doi"] = doi
                    logger.info(f"Found DOI for {self.entry['ID']} : {doi}")
                    return doi
                # if item.has_key("ISSN"):
                #     self.entry["issn"] = item["ISSN"]
                # if item.has_key("ISBN"):
                #     self.entry["isbn"] = item["ISBN"]
        return None


class DBLPLookup(Lookup):
    """Lookup for info on https://dlbp.org
    Uses the API documented here:
    https://dblp.org/faq/13501473.html"""

    domain = "dblp.org"
    path = "/search/publ/api"

    def get_params(self) -> Dict[str, str]:
        return {"format": "json", "h": "3", "q": self.entry["author"]}

    def handle_output(self, data) -> Optional[str]:
        try:
            data = JSONDecoder().decode(data.decode())
        except JSONDecodeError:
            return None
        print(data)
        return None
