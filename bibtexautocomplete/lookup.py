from typing import Dict, Optional
from urllib.parse import urlencode

from httplib import HTTPSConnection

from .constants import EntryType


class Lookup:
    """Abstract class to wrap queries"""

    domain: str
    host: Optional[str] = None  # specify when different to domain
    path: str = "/"
    request: str = "GET"
    default_headers: Dict[str, str] = {
        "User-Agent": "Mozilla/5.0",
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

    def get_params(self) -> Dict[str, str]:
        """Query parameters, can use self.entry to set them"""
        raise NotImplementedError()

    def lookup(self) -> bool:
        """main lookup function
        returns true if the lookup succeeded in finding all info
        false otherwise"""
        connection = HTTPSConnection(self.get_domain())
        connection.request(
            self.get_request(),
            self.get_path(),
            self.get_params(),
            self.get_headers(),
        )
        response = connection.getresponse()
        connection.close()
        if response.status != 200:
            return False
        data = response.read()
        return self.handle_output(data)

    def handle_output(self, data: str) -> bool:
        """Should modify self.entry with data extracted from data here"""
        raise NotImplementedError()

    def __init__(self, entry: EntryType) -> None:
        self.entry = entry


print(urlencode({"author": "hello my name is"}))

"https://api.crossref.org/works?query.author=Seger&query.title=Ethnoarchaeology"
