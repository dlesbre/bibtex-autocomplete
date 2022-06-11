"""
Lookup info from https://unpaywall.org/
"""

from typing import Dict, Iterable, List, Optional
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

    Example urls:
    DOI mode:
    https://api.unpaywall.org/v2/10.1109/tro.2004.829459?email=some.test%40gmail.com

    Title mode:
    https://api.unpaywall.org/v2/search/?email=some.test%40gmail.com&query=Reactive+Path+Deformation+for+Nonholonomic+Mobile+Robots
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

    def get_results(self, data: bytes) -> Optional[Iterable[SafeJSON]]:
        json = SafeJSON.from_bytes(data)
        if self.doi is not None:
            # doi based search, single result if any
            return [json]
        return json["results"].iter_list()

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
            # Unknown month are set to first january...
            if date[4:] != "-01-01" and len(date) >= 7:
                month = date[5:7]
        values = BibtexEntry()

        title = result["journal_name"].to_str()
        is_journal = result["genre"].to_str() == "journal-article"

        values.author = self.get_authors(result["z_authors"])
        values.booktitle = None if is_journal else title
        values.doi = result["doi"].to_str()
        values.issn = result["journal_issn_l"].to_str()
        values.journal = title if is_journal else None
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
        FieldNames.JOURNAL,
        FieldNames.MONTH,
        FieldNames.PUBLISHER,
        FieldNames.TITLE,
        FieldNames.URL,
        FieldNames.YEAR,
    }
