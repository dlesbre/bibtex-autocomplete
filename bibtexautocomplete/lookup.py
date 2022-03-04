# Explicit lookups for DOI searches

from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote_plus, urlencode

from .abstractlookup import JSONLookup, LookupType
from .bibtex import Author, BibtexEntry
from .defs import EMAIL, SafeJSON, extract_doi


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
    def get_authors(authors: SafeJSON) -> List[Author]:
        """Parses JSON output into bibtex formatted author list"""
        formatted = []
        for author in authors.iter_list():
            if not isinstance(author, dict):
                continue
            lastname = author["family"].to_str()
            if lastname is not None:
                formatted.append(Author(lastname, author["given"].to_str()))
        return formatted

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

    def get_value(self, result: SafeJSON) -> BibtexEntry:
        """Extract bibtex data from JSON output"""
        year, month = self.get_date(result)
        values = BibtexEntry()
        values.doi = extract_doi(self.get_doi(result))
        values.issn = result["ISSN"][0].to_str()
        values.isbn = result["ISBN"][0].to_str()
        values.title = self.get_title(result)
        values.author = self.get_authors(result["author"])
        values.booktitle = result["container-title"][0].to_str()
        values.volume = result["volume"].to_str()
        values.pages = result["page"].to_str()
        values.publisher = result["publisher"].to_str()
        values.year = year
        values.month = month
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
    def get_authors(info: SafeJSON) -> List[Author]:
        """Return a bibtex formatted list of authors"""
        authors = info["authors"]["author"]
        formatted = []
        for author in authors.iter_list():
            aut = Author.from_name(author["text"].to_str())
            if aut is not None:
                formatted.append(aut)
        return formatted

    def get_value(self, result: SafeJSON) -> BibtexEntry:
        info = result["info"]
        values = BibtexEntry()
        values.doi = extract_doi(self.get_doi(result))
        values.title = info["title"].to_str()
        values.pages = info["pages"].to_str()
        values.volume = info["volume"].to_str()
        values.year = info["year"].to_str()
        values.author = self.get_authors(info)
        values.url = info["ee"].to_str() if info["access"].to_str() == "open" else None
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
    def get_authors(authors: SafeJSON) -> List[Author]:
        """Return a bibtex formatted list of authors"""
        formatted = []
        for author in authors.iter_list():
            aut = Author.from_name(author["alias"]["name"].to_str())
            if aut is not None:
                formatted.append(aut)
        return formatted

    def get_value(self, result: SafeJSON) -> BibtexEntry:
        page_1 = result["firstpage"].to_str()
        page_n = result["lastpage"].to_str()
        values = BibtexEntry()
        values.doi = extract_doi(self.get_doi(result))
        values.booktitle = result["booktitle"].to_str()
        values.volume = result["volume"].to_str()
        values.number = result["number"].to_str()
        values.address = result["address"].to_str()
        values.organization = result["organization"].to_str()
        values.publisher = result["publisher"].to_str()
        values.year = result["year"].to_str()
        values.month = result["month"].to_str()
        values.title = result["title"].to_str()
        values.pages = (
            f"{page_1}-{page_n}" if page_1 is not None and page_n is not None else None
        )
        values.author = self.get_authors(result["authors"])
        values.editor = self.get_authors(result["editors"])
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

    def get_results(self, data) -> Optional[Iterable[SafeJSON]]:
        json = SafeJSON.from_bytes(data)
        if self.doi is not None:
            # doi based search, single result if any
            return [json]
        return json["results"].iter_list()

    def get_title(self, result: SafeJSON) -> Optional[str]:
        """Get the title of a result"""
        return result["response"]["title"].to_str()

    def get_doi(self, result: SafeJSON) -> Optional[str]:
        return extract_doi(result["doi"].to_str())

    @staticmethod
    def get_authors(authors: SafeJSON) -> List[Author]:
        """Return a bibtex formatted list of authors"""
        formatted = []
        for author in authors.iter_list():
            family = author["family"].to_str()
            if family is not None:
                given = author["given"].to_str()
                formatted.append(Author(family, given))
        return formatted

    def get_value(self, result: SafeJSON) -> BibtexEntry:
        result = result["response"]
        date = result["published_date"].to_str()  # ISO format YYYY-MM-DD
        year = str(result["year"].to_int())
        month = None
        if date is not None:
            if year is None and len(date) >= 4:
                year = date[0:4]
            if len(date) >= 7:
                month = date[5:7]
        values = BibtexEntry()
        values.doi = extract_doi(result["doi"].to_str())
        values.booktitle = result["journal_name"].to_str()
        values.publisher = result["publisher"].to_str()
        values.title = result["title"].to_str()
        values.year = year
        values.month = month
        values.url = result["best_oa_location"]["url_for_pdf"].to_str()
        values.issn = result["journal_issn_l"].to_str()
        values.author = self.get_authors(result["z_authors"])
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
