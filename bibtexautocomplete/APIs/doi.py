"""
Queries to https://doi.org/<doi>
used to check that dois are valid
"""

from typing import Optional
from urllib.parse import quote

from ..bibtex.normalize import normalize_doi, normalize_str_weak, normalize_url
from ..lookups.abstract_base import Data
from ..lookups.condition_mixin import ConditionMixin
from ..lookups.https import HTTPSRateCapedLookup, RedirectFollower
from ..utils.logger import logger
from ..utils.safe_json import SafeJSON


class URLCheck(
    ConditionMixin[str, Optional[Data]], RedirectFollower[str, Optional[Data]]
):
    """Checks that an URL exists (should return 200)
    Follows redirection (up to a certain depth)"""

    name = "url_checker"
    accept = "text/html"
    silent_fail = True

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
    """
    Queries https://doi.org/api/handles/<doi> to check DOI exists
    and get redirection URL, then checks the redirection URL returns 200
    or redirects to an URL that does.

    Example URL: https://doi.org/api/handles/10.1109/tro.2004.829459
    """

    name = "doi_checker"
    silent_fail = True

    params = {"type": "URL"}
    domain = "doi.org"
    path = "/api/handles/"

    not_available_checks = [
        "doi not available",
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

    def get_base_path(self) -> str:
        return self.path + quote(self.doi)

    def process_data(self, data: Data) -> Optional[bool]:
        if data.code != 200:
            return None
        json = SafeJSON.from_bytes(data.data)
        if json["responseCode"].to_int() != 1:
            return None
        for value in json["values"].iter_list():
            if value["type"].to_str() == "URL":
                if self.check_url(value["data"]["value"].to_str()):
                    return True
        return None

    def check_url(self, url: Optional[str]) -> bool:
        if url is not None:
            checker = URLCheck(url)
            final = checker.query()
            if final is not None and checker.response is not None:
                # don't try to read content if not text
                info = checker.response.headers
                if info.get_content_maintype() != "text":
                    return True
                # Some websites, namely springer, don't send 404 for invalid DOIs...
                # See: https://link.springer.com/deleted
                try:
                    text = normalize_str_weak(final.data.decode())
                    for elem in self.not_available_checks:
                        if elem in text:
                            logger.debug("INVALID TEXT IN RESPONSE PAGE " + elem)
                            return False
                except UnicodeDecodeError:
                    logger.warn("Can't decode text content from URL {}".format(url))
                return True
        return False
