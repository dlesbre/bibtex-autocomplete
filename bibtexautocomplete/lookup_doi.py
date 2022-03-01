# Explicit lookups for DOI searches

from typing import Any, Dict, Iterable, Optional

from .lookup import AbstractLookup


class CrossrefLookup(AbstractLookup):
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

    def get_value(self, result: Dict[str, Any]) -> Optional[str]:
        if "DOI" in result:
            return result["DOI"]
        return None


class DBLPLookup(AbstractLookup):
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

    def get_value(self, result: Dict[str, Any]) -> Optional[str]:
        if "info" in result and "doi" in result["info"]:
            return result["info"]["doi"]
        return None
