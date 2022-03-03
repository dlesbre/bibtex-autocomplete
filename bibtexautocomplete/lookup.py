# Explicit lookups for DOI searches

from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote_plus, urlencode

from .abstractlookup import JSONLookup, LookupType
from .bibtex import Author
from .defs import EMAIL, ResultType, SafeJSON, extract_doi


class CrossrefLookup(JSONLookup):
    """Lookup info on https://www.crossref.org
    Uses the crossref REST API, documentated here:
    https://api.crossref.org/swagger-ui/index.html
    """

    name = "crossref"

    domain = "api.crossref.org"
    path = "/works"

    def get_params(self) -> Dict[str, str]:
        base = {"rows": "3"}
        if self.title is not None:
            base["query.title"] = self.title
        if self.author is not None:
            base["query.author"] = self.author
        return base

    def get_results(self, data) -> Optional[Iterable[SafeJSON]]:
        """Return the result list"""
        json = SafeJSON.from_bytes(data)
        if json["status"].to_str() == "ok":
            return json["message"]["items"].iter_list()
        return None

    def get_title(self, result: SafeJSON) -> Optional[str]:
        """Get the title of a result"""
        return result["title"][0].to_str()

    def get_doi(self, result: SafeJSON) -> Optional[str]:
        """Get the DOI of a result"""
        return result["DOI"].to_str()

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
    def get_date(result: SafeJSON) -> Tuple[Optional[str], Optional[str]]:
        date = None
        for field in (
            "published-print",
            "issued",
            "published-online",
            "created",
            "content-created",
        ):
            date = result[field]["date-parts"][0]
            year = date[0].force_str()
            month = date[1].force_str()
            if year is not None:
                return year, month
        return None, None

    def get_value(self, result: SafeJSON) -> ResultType:
        """Extract bibtex data from JSON output"""
        year, month = self.get_date(result)
        values = {
            "doi": extract_doi(self.get_doi(result)),
            "issn": result["ISSN"][0].to_str(),
            "isbn": result["ISBN"][0].to_str(),
            "title": self.get_title(result),
            "author": self.get_authors(result["author"].to_str()),
            "booktitle": result["container-title"][0].to_str(),
            "volume": result["volume"].to_str(),
            "pages": result["page"].to_str(),
            "publisher": result["publisher"].to_str(),
            "year": year,
            "month": month,
        }
        return values

    fields = (
        "doi",
        "issn",
        "isbn",
        "title",
        "booktitle",
        "volume",
        "pages",
        "publisher",
        "year",
        "month",
        "author",
        "url",
    )


class DBLPLookup(JSONLookup):
    """Lookup for info on https://dlbp.org
    Uses the API documented here:
    https://dblp.org/faq/13501473.html"""

    name = "dblp"

    domain = "dblp.org"
    path = "/search/publ/api"

    def get_params(self) -> Dict[str, str]:
        search = ""
        if self.author is not None:
            search += self.author + " "
        if self.title is not None:
            search += self.title + " "
        return {"format": "json", "h": "3", "q": search.strip()}

    def get_results(self, data) -> Iterable[SafeJSON]:
        """Return the result list"""
        return SafeJSON.from_bytes(data)["result"]["hits"]["hit"].iter_list()

    def get_title(self, result: SafeJSON) -> Optional[str]:
        """Get the title of a result"""
        return result["info"]["title"].to_str()

    def get_doi(self, result: SafeJSON) -> Optional[str]:
        """Get the DOI of a result"""
        return result["info"]["doi"].to_str()

    @staticmethod
    def get_authors(info: SafeJSON) -> Optional[str]:
        """Return a bibtex formatted list of authors"""
        authors = info["authors"]["author"]
        formatted = []
        for author in authors.iter_list():
            name = author["text"].to_str()
            if name is not None:
                formatted.append(name)
        return " and ".join(formatted)

    def get_value(self, result: SafeJSON) -> ResultType:
        info = result["info"]
        values = {
            "doi": extract_doi(self.get_doi(result)),
            "title": info["title"].to_str(),
            "pages": info["pages"].to_str(),
            "volume": info["volume"].to_str(),
            "year": info["year"].to_str(),
            "author": self.get_authors(info),
            "url": info["ee"].to_str() if info["access"].to_str() == "open" else None,
        }
        return values

    fields = ("doi", "title", "pages", "volume", "year", "author", "url")


class ResearchrLookup(JSONLookup):
    """Lookup for info on https://researchr.org/
    Uses the API documented here:
    https://researchr.org/about/api"""

    name = "researchr"

    domain = "researchr.org"
    path = "/api/search/publication/"

    def get_path(self) -> str:
        search = ""
        if self.author is not None:
            search += self.author + " "
        if self.title is not None:
            search += self.title + " "
        return self.path + quote_plus(search.strip())

    def get_results(self, data) -> Iterable[SafeJSON]:
        """Return the result list"""
        return SafeJSON.from_bytes(data)["result"].iter_list()

    def get_title(self, result: SafeJSON) -> Optional[str]:
        """Get the title of a result"""
        return result["title"].to_str()

    def get_doi(self, result: SafeJSON) -> Optional[str]:
        """Get the DOI of a result"""
        return result["doi"].to_str()

    @staticmethod
    def get_authors(authors: SafeJSON) -> Optional[str]:
        """Return a bibtex formatted list of authors"""
        formatted = []
        for author in authors.iter_list():
            name = author["alias"]["name"].to_str()
            if name is not None:
                formatted.append(name)
        if formatted:
            return " and ".join(formatted)
        return None

    def get_value(self, result: SafeJSON) -> ResultType:
        page_1 = result["firstpage"].to_str()
        page_n = result["lastpage"].to_str()
        values = {
            "doi": extract_doi(self.get_doi(result)),
            "booktitle": result["booktitle"].to_str(),
            "volume": result["volume"].to_str(),
            "number": result["number"].to_str(),
            "address": result["address"].to_str(),
            "organization": result["organization"].to_str(),
            "publisher": result["publisher"].to_str(),
            "year": result["year"].to_str(),
            "month": result["month"].to_str(),
            "title": result["title"].to_str(),
            "pages": f"{page_1}-{page_n}"
            if page_1 is not None and page_n is not None
            else None,
            "author": self.get_authors(result["authors"]),
            "editor": self.get_authors(result["editors"]),
        }
        return values

    fields = (
        "doi",
        "booktitle",
        "volume",
        "number",
        "address",
        "organization",
        "publisher",
        "pages",
        "editor",
        "title",
        "year",
        "month",
        "url",
        "issn",
        "author",
    )


class UnpaywallLookup(JSONLookup):
    """Lookup on https://unpaywall.org/
    only if the entry has a known DOI
    API documented at:
    https://unpaywall.org/products/api
    """

    name = "unpaywall"

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

    def get_results_json(self, data) -> Optional[Iterable[SafeJSON]]:
        if self.doi is not None:
            # doi based search
            # single result if any
            return [data]
        return data.get("result")

    def get_title(self, result: SafeJSON) -> Optional[str]:
        """Get the title of a result"""
        return result["title"].to_str()

    def matches_entry(self, result: SafeJSON) -> bool:
        """Always true in DOI mode (single result)"""
        return self.doi is not None or super().matches_entry(result)

    @staticmethod
    def get_authors(authors: SafeJSON) -> Optional[str]:
        """Return a bibtex formatted list of authors"""
        formatted = []
        for author in authors.iter_list():
            family = author["family"].to_str()
            if family is not None:
                given = author["given"].to_str()
                formatted.append(Author(family, given).to_bibtex())
        if formatted:
            return " and ".join(formatted)
        return None

    def get_value(self, result: SafeJSON) -> ResultType:
        date = result["published_date"].to_str()  # ISO format YYYY-MM-DD
        year = str(result["year"].to_int())
        month = None
        if date is not None:
            if year is None and len(date) >= 4:
                year = date[0:4]
            if len(date) >= 7:
                month = date[5:7]
        values = {
            "doi": extract_doi(result["doi"].to_str()),
            "booktitle": result["journal_name"].to_str(),
            "publisher": result["publisher"].to_str(),
            "title": result["title"].to_str(),
            "year": year,
            "month": month,
            "url": result["best_oa_location"]["url_for_pdf"].to_str(),
            "issn": result["journal_issn_l"].to_str(),
            "author": self.get_authors(result["z_authors"]),
        }
        return values

    fields = (
        "doi",
        "booktitle",
        "publisher",
        "title",
        "year",
        "month",
        "url",
        "issn",
        "author",
    )


# List of lookup to use, in the order they will be used
LOOKUPS: List[LookupType] = [
    CrossrefLookup,
    DBLPLookup,
    ResearchrLookup,
    UnpaywallLookup,
]
LOOKUP_NAMES = [cls.name for cls in LOOKUPS]
