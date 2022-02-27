from http.client import HTTPSConnection
from json import JSONDecodeError, JSONDecoder
from logging import info as log
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from .constants import USER_AGENT, EntryType


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
        return self.path

    def get_params(self) -> Optional[Any]:
        """Query parameters, can use self.entry to set them"""
        return None

    def lookup(self) -> bool:
        """main lookup function
        returns true if the lookup succeeded in finding all info
        false otherwise"""
        domain = self.get_domain()
        request = self.get_request()
        path = self.get_path()
        log(f"{request} {domain} {path}")
        connection = HTTPSConnection(domain)
        connection.request(
            request,
            path,
            self.get_params(),
            self.get_headers(),
        )
        response = connection.getresponse()
        connection.close()
        log(f"response: {response.status} {response.reason}")
        if response.status != 200:
            return False
        data = response.read()
        return self.handle_output(data)

    def handle_output(self, data: bytes) -> bool:
        """Should modify self.entry with data extracted from data here"""
        raise NotImplementedError()

    def complete(self) -> bool:
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

    def get_path(self):
        return (
            self.path
            + "?"
            + urlencode(
                {
                    "rows": "3",
                    "query.author": self.entry["author"],
                    "query.title": self.entry["title"],
                }
            )
        )

    def handle_output(self, data):
        try:
            data = JSONDecoder().decode(data.decode())
        except JSONDecodeError:
            return False
        if data["status"] != "ok":
            return False
        items = data["message"]["items"]
        for item in items:
            print(item.keys())
            print(item["DOI"][0])
            print(item["title"][0])
            print(item["author"][0]["family"])
        # print(items)
        return True
