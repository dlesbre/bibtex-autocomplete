# Explicit lookups for DOI searches

from typing import Any, Dict, Iterable, Optional
from urllib.parse import quote_plus, urlencode

from .abstractlookup import ADOITitleLookup, AJSONSearchLookup, ALookup
from .defs import EMAIL, ResultType, extract_doi


class CrossrefLookup(ALookup):
    """Lookup info on https://www.crossref.org
    Uses the crossref REST API, documentated here:
    https://api.crossref.org/swagger-ui/index.html
    """

    domain = "api.crossref.org"
    path = "/works"

    def get_params(self) -> Dict[str, str]:
        base = {"rows": "3"}
        if self.title is not None:
            base["query.title"] = self.title
        if self.author is not None:
            base["query.author"] = self.author
        return base

    def get_results_json(self, data) -> Optional[Iterable[Dict[str, Any]]]:
        """Return the result list"""
        if "status" in data and data["status"] == "ok":
            return data["message"]["items"]
        return None

    def get_title(self, result: Dict[str, Any]) -> Optional[str]:
        """Get the title of a result"""
        if "title" in result:
            return result["title"][0]
        return None

    def get_value(self, result: Dict[str, Any]) -> ResultType:
        if "DOI" in result:
            return {"doi": extract_doi(result["DOI"])}
        return dict()


class DBLPLookup(ALookup):
    """Lookup for info on https://dlbp.org
    Uses the API documented here:
    https://dblp.org/faq/13501473.html"""

    domain = "dblp.org"
    path = "/search/publ/api"

    def get_params(self) -> Dict[str, str]:
        search = ""
        if self.author is not None:
            search += self.author + " "
        if self.title is not None:
            search += self.title + " "
        return {"format": "json", "h": "3", "q": search.strip()}

    def get_results_json(self, data) -> Optional[Iterable[Dict[str, Any]]]:
        """Return the result list"""
        try:
            return data["result"]["hits"]["hit"]
        except KeyError:
            return None

    def get_title(self, result: Dict[str, Any]) -> Optional[str]:
        """Get the title of a result"""
        if "info" in result and "title" in result["info"]:
            return result["info"]["title"]
        return None

    def get_value(self, result: Dict[str, Any]) -> ResultType:
        if "info" in result and "doi" in result["info"]:
            return {"doi": extract_doi(result["info"]["doi"])}
        return dict()


class ResearchrLookup(ALookup):
    """Lookup for info on https://researchr.org/
    Uses the API documented here:
    https://researchr.org/about/api"""

    domain = "researchr.org"
    path = "/api/search/publication/"

    def get_path(self) -> str:
        search = ""
        if self.author is not None:
            search += self.author + " "
        if self.title is not None:
            search += self.title + " "
        return self.path + quote_plus(search.strip())

    def get_results_json(self, data) -> Optional[Iterable[Dict[str, Any]]]:
        """Return the result list"""
        if "result" in data:
            return data["result"]
        return None

    def get_title(self, result: Dict[str, Any]) -> Optional[str]:
        """Get the title of a result"""
        if "title" in result:
            return result["title"]
        return None

    def get_value(self, result: Dict[str, Any]) -> ResultType:
        if "doi" in result:
            return {"doi": extract_doi(result["doi"])}
        return dict()


class UnpaywallLookup(ADOITitleLookup, AJSONSearchLookup[Dict[str, Any]]):
    """Lookup on https://unpaywall.org/
    only if the entry has a known DOI
    API documented at:
    https://unpaywall.org/products/api
    """

    domain = "api.unpaywall.org"
    path = "/v2/"

    params = {"email": EMAIL}

    doi: Optional[str] = None
    title: Optional[str] = None

    def get_params(self) -> Dict[str, str]:
        base = super().get_params()
        if self.doi is None:
            if self.title is None:
                raise ValueError("query with no title or doi")
            base["query"] = self.title
        return base

    def get_path(self) -> str:
        base = self.path
        params = "?" + urlencode(self.get_params())
        if self.doi is not None:
            return base + self.doi + params
        return base + "search/" + params

    def get_results_json(self, data) -> Optional[Iterable[Dict[str, Any]]]:
        print(data)
        return None
