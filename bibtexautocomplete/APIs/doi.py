"""
Queries to https://doi.org/<doi>
used to check that dois are valid
"""

from typing import Optional
from urllib.parse import quote, urlencode

from ..bibtex.normalize import normalize_doi, normalize_str_weak, normalize_url
from ..lookups.abstract_base import Data
from ..lookups.condition_mixin import ConditionMixin
from ..lookups.https import HTTPSRateCapedLookup, RedirectFollower
from ..utils.safe_json import SafeJSON


class URLCheck(
    ConditionMixin[str, Optional[Data]], RedirectFollower[str, Optional[Data]]
):
    """Checks that an URL exists (should return 200)
    Follows redirection (up to a certain depth)"""

    name = "url_checker"
    accept = "text/html"

    def condition(self) -> bool:
        return self.is_valid

    def __init__(self, input: str):
        split = normalize_url(input)
        if split is None:
            self.is_valid = False
        else:
            self.is_valid = True
            self.domain = split[0]
            self.path = split[1]

    def process_data(self, data: Data) -> Optional[Data]:
        if data.code != 200:
            return None
        return data


class DOICheck(
    ConditionMixin[str, Optional[bool]],
    HTTPSRateCapedLookup[str, Optional[bool]],
):

    name = "doi_checker"

    params = {"type": "URL"}
    domain = "doi.org"
    path = "/api/handles/"

    not_available_checks = [
        "not available",
        "not found",
    ]

    doi: str

    def __init__(self, input: str) -> None:
        self.input = input

    def condition(self) -> bool:
        """Checks that a doi is valid"""
        doi = normalize_doi(self.input)
        if doi is not None:
            self.doi = doi
            return True
        return False

    def get_path(self) -> str:
        return self.path + quote(self.doi) + "?" + urlencode(self.params)

    def process_data(self, data: Data) -> Optional[bool]:
        if data.code != 200:
            return None
        json = SafeJSON.from_bytes(data.data)
        if json["responseCode"].to_int() != 1:
            return None
        for value in json["values"].iter_list():
            if value["type"].to_str() == "URL":
                return self.check_url(value["data"]["value"].to_str())
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
