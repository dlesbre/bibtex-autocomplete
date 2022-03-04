"""
Lookup info from https://unpaywall.org/
"""

from typing import Iterable, Optional
from urllib.parse import urlencode

from ..bibtex.author import Author
from ..bibtex.entry import BibtexEntry, FieldNames
from ..lookups.lookups import JSON_DT_Lookup
from ..utils.constants import EMAIL
from ..utils.safe_json import SafeJSON


class UnpaywallLookup(JSON_DT_Lookup):
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

    def get_params(self) -> dict[str, str]:
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
        return result["doi"].to_str()

    @staticmethod
    def get_authors(authors: SafeJSON) -> list[Author]:
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

        values.author = self.get_authors(result["z_authors"])
        values.booktitle = result["journal_name"].to_str()
        values.doi = result["doi"].to_str()
        values.issn = result["journal_issn_l"].to_str()
        values.month = month
        values.publisher = result["publisher"].to_str()
        values.title = result["title"].to_str()
        values.url = result["best_oa_location"]["url_for_pdf"].to_str()
        values.year = year

        return values

    fields = {
        FieldNames.AUTHOR,
        FieldNames.BOOKTITLE,
        FieldNames.DOI,
        FieldNames.ISSN,
        FieldNames.MONTH,
        FieldNames.PUBLISHER,
        FieldNames.TITLE,
        FieldNames.URL,
        FieldNames.YEAR,
    }
