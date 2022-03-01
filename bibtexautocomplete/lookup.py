# Explicit lookups for DOI searches

from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote_plus, urlencode

from .abstractlookup import ADOITitleLookup, AJSONSearchLookup, ALookup
from .bibtex import Author
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

    @staticmethod
    def get_0(obj: Optional[List[str]]) -> Optional[str]:
        """Get first element if it exists"""
        if obj is None:
            return None
        return obj[0]

    @staticmethod
    def get_authors(authors: Any) -> Optional[str]:
        """Parses JSON output into bibtex formatted author list"""
        if isinstance(authors, list):
            formatted = []
            for author in authors:
                if not isinstance(author, dict):
                    continue
                lastname = author.get("family")
                if lastname is not None:
                    formatted.append(Author(lastname, author.get("given")).to_bibtex())
            return " and ".join(formatted)
        return None

    @staticmethod
    def get_date(result: Dict[str, Any], values: ResultType) -> ResultType:
        date = None
        for field in (
            "published-print",
            "issued",
            "published-online",
            "created",
            "content-created",
        ):
            if field in result:
                date = result[field]
        if date is None:
            return values
        parts = CrossrefLookup.get_0(date.get("date-parts"))
        if parts is not None:
            values["year"] = str(parts[0])
            if len(parts) >= 2:
                values["month"] = str(parts[1])
        return values

    def get_value(self, result: Dict[str, Any]) -> ResultType:
        """Extract bibtex data from JSON output"""
        values = {
            "doi": extract_doi(result.get("DOI")),
            "issn": self.get_0(result.get("ISSN")),
            "isbn": self.get_0(result.get("ISBN")),
            "title": self.get_title(result),
            "author": self.get_authors(result.get("author")),
            "booktitle": self.get_0(result.get("container-title")),
            "volume": result.get("volume"),
            "page": result.get("page"),
            "publisher": result.get("publisher"),
        }
        return self.get_date(result, values)


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

    @staticmethod
    def get_authors(info: Any) -> Optional[str]:
        """Return a bibtex formatted list of authors"""
        authors = info.get("authors")
        if authors is None:
            return None
        authors = authors.get("author")
        if isinstance(authors, list):
            formatted = []
            for author in authors:
                name = author.get("text")
                if name is not None:
                    formatted.append(name)
            return " and ".join(formatted)
        return None

    def get_value(self, result: Dict[str, Any]) -> ResultType:
        values = dict()
        if "info" in result:
            info = result["info"]
            values = {
                "doi": extract_doi(info.get("doi")),
                "title": info.get("title"),
                "pages": info.get("pages"),
                "volume": info.get("volume"),
                "year": info.get("year"),
                "author": self.get_authors(info),
                "url": info.get("ee") if info.get("access") == "open" else None,
            }
        return values


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
        return data.get("result")

    def get_title(self, result: Dict[str, Any]) -> Optional[str]:
        """Get the title of a result"""
        return result.get("title")

    @staticmethod
    def get_authors(authors: Any) -> Optional[str]:
        """Return a bibtex formatted list of authors"""
        if isinstance(authors, list):
            formatted = []
            for author in authors:
                alias = author.get("alias")
                if isinstance(alias, dict):
                    name = alias.get("name")
                    if name is not None:
                        formatted.append(name)
            return " and ".join(formatted)
        return None

    def get_value(self, result: Dict[str, Any]) -> ResultType:
        page_1 = result.get("firstpage")
        page_n = result.get("lastpage")
        values = {
            "doi": extract_doi(result.get("doi")),
            "booktitle": result.get("booktitle"),
            "volume": result.get("volume"),
            "number": result.get("number"),
            "address": result.get("address"),
            "organization": result.get("organization"),
            "publisher": result.get("publisher"),
            "year": result.get("year"),
            "month": result.get("month"),
            "title": result.get("title"),
            "pages": f"{page_1}-{page_n}"
            if page_1 is not None and page_n is not None
            else None,
            "authors": self.get_authors(result.get("authors")),
            "editors": self.get_authors(result.get("editors")),
        }
        return values


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
        if self.doi is not None:
            # doi based search
            # single result if any
            return [data]
        return data.get("result")

    def get_title(self, result: Dict[str, Any]) -> Optional[str]:
        """Get the title of a result"""
        return result.get("title")

    def matches_entry(self, result: Dict[str, Any]) -> bool:
        """Always true in DOI mode (single result)"""
        return self.doi is not None or super().matches_entry(result)

    @staticmethod
    def get_authors(authors: Any) -> Optional[str]:
        """Return a bibtex formatted list of authors"""
        if isinstance(authors, list):
            formatted = []
            for author in authors:
                family = author.get("family")
                if family is not None:
                    given = author.get("given")
                    formatted.append(Author(family, given).to_bibtex())
            return " and ".join(formatted)
        return None

    def get_value(self, result: Dict[str, Any]) -> ResultType:
        date = result.get("published_date")  # ISO format YYYY-MM-DD
        year = str(result.get("year"))
        month = None
        if date is not None:
            if year is None and len(date) >= 4:
                year = date[0:4]
            if len(date) >= 7:
                month = date[5:7]

        values = {
            "doi": extract_doi(result.get("doi")),
            "booktitle": result.get("journal_name"),
            "publisher": result.get("publisher"),
            "title": result.get("title"),
            "year": year,
            "month": month,
            "url": result.get("best_oa_location"),
            "issn": result.get("journal_issn_l"),
            "authors": self.get_authors(result.get("z_authors")),
        }
        return values
