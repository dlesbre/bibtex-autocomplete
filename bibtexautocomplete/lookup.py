from http.client import HTTPSConnection
from json import JSONDecodeError, JSONDecoder
from logging import info as log
from typing import Any, Dict, Optional
from urllib.parse import urlencode

# from .bibtex import Author, get_authors
from .constants import CONNECTION_TIMEOUT, USER_AGENT, EntryType, str_similar


class Lookup:
    """Abstract class to wrap queries"""

    domain: str
    host: Optional[str] = None  # specify when different to domain
    path: str = "/"
    request: str = "GET"
    default_headers: Dict[str, str] = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/json",
    }
    headers: Dict[str, str] = {}
    params: Dict[str, str] = {}

    entry: EntryType

    def get_headers(self) -> Dict[str, str]:
        """Return the headers used in an HTTPS request"""
        headers = self.default_headers.copy()
        headers.update(self.headers)
        headers["host"] = self.get_host()
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
        log(f"{request} {domain} {path}")
        connection = HTTPSConnection(domain, timeout=CONNECTION_TIMEOUT)
        connection.request(
            request,
            path,
            self.get_body(),
            self.get_headers(),
        )
        response = connection.getresponse()
        connection.close()
        log(f"response: {response.status} {response.reason}")
        if response.status != 200:
            return None
        data = response.read()
        return self.handle_output(data)

    def handle_output(self, data: bytes) -> Optional[str]:
        """Should modify self.entry with data extracted from data here"""
        raise NotImplementedError()

    def complete(self) -> Optional[str]:
        """Tries to complete an entry
        override this to make multiple requests
        (i.e. try different search terms)"""
        return self.lookup()

    def __init__(self, entry: EntryType) -> None:
        self.entry = entry


class CrossrefLookup(Lookup):
    """Lookup info on crossref"""

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
                    log(f"Found DOI for {self.entry['ID']} : {doi}")
                    return doi
                # if item.has_key("ISSN"):
                #     self.entry["issn"] = item["ISSN"]
                # if item.has_key("ISBN"):
                #     self.entry["isbn"] = item["ISBN"]
        return None
