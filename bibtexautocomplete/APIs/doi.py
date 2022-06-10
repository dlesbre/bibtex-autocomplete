"""
Queries to https://doi.org/<doi>
used to check that dois are valid
"""

from typing import Iterator, List, Optional
from urllib.parse import quote, urlencode, urlsplit

from ..bibtex.normalize import normalize_str_weak
from ..lookups.abstract_base import Data
from ..lookups.https import HTTPSRateCapedLookup, RedirectFollower
from ..lookups.multiple_mixin import MultipleQueryMixin
from ..utils.safe_json import SafeJSON


class URLCheck(RedirectFollower[str, Optional[Data]]):
    """Checks that an URL exists (should return 200)
    Follows redirection (up to a certain depth)"""

    accept = "text/html"

    def __init__(self, input: str):
        split = urlsplit(input)
        self.domain = split.netloc
        self.path = f"{split.path}?{split.query}"

    def process_data(self, data: Data) -> Optional[Data]:
        if data.code != 200:
            return None
        return data


class DOICheck(
    MultipleQueryMixin[List[str], Optional[str]],
    HTTPSRateCapedLookup[List[str], Optional[str]],
):

    name = "doi"

    params = {"type": "URL"}
    domain = "doi.org"
    path = "/api/handles/"

    doi: str
    index: int

    not_available_checks = [
        "not available",
        "not found",
    ]

    def iter_queries(self) -> Iterator[None]:
        for i, doi in enumerate(self.dois):
            self.doi = doi
            self.index = i
            yield None

    def __init__(self, input: List[str]) -> None:
        self.dois = input

    def get_path(self) -> str:
        return self.path + quote(self.doi) + "?" + urlencode(self.params)

    def process_data(self, data: Data) -> Optional[str]:
        if data.code != 200:
            return None
        json = SafeJSON.from_bytes(data.data)
        if json["responseCode"].to_int() != 1:
            return None
        for value in json["values"].iter_list():
            if value["type"].to_str() == "URL":
                if self.check_url(value["data"]["value"].to_str()):
                    return self.doi
        return None

    def check_url(self, url: Optional[str]) -> bool:
        if url is not None:
            checker = URLCheck(url)
            final = checker.query()
            if final is not None:
                text = normalize_str_weak(final.data.decode())
                # Some website, namely springer, don't send 404 for invalid DOIs...
                # See: https://link.springer.com/deleted
                for elem in self.not_available_checks:
                    if elem in text:
                        return False
                return True
        return False


D = DOICheck(["10.1007/978-1-4684-5287-7", "10.1109/5.771073", "not a doi"])
D.query()
