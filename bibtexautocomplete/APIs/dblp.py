"""
Lookup info from https://dlbp.org
"""

from typing import Dict, Iterable, List

from ..bibtex.author import Author
from ..bibtex.entry import BibtexEntry, FieldNames
from ..lookups.lookups import JSON_AT_Lookup
from ..utils.constants import QUERY_MAX_RESULTS
from ..utils.safe_json import SafeJSON


class DBLPLookup(JSON_AT_Lookup):
    """Lookup for info on https://dlbp.org
    Uses the API documented here:
    https://dblp.org/faq/13501473.html

    example URLs:
    no DOI mode.
    Author+title mode:
    https://dblp.org/search/publ/api?format=json&h=3&q=Lamiraux+Reactive+Path+Deformation+for+Nonholonomic+Mobile+Robots
    """

    name = "dblp"

    domain = "dblp.org"
    path = "/search/publ/api"

    def get_params(self) -> Dict[str, str]:
        search = ""
        if self.author is not None:
            search += self.author + " "
        if self.title is not None:
            search += self.title + " "
        return {"format": "json", "h": str(QUERY_MAX_RESULTS), "q": search.strip()}

    def get_results(self, data: bytes) -> Iterable[SafeJSON]:
        """Return the result list"""
        return SafeJSON.from_bytes(data)["result"]["hits"]["hit"].iter_list()

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
        values.author = self.get_authors(info)
        values.doi = info["doi"].to_str()
        values.pages = info["pages"].to_str()
        values.title = info["title"].to_str()
        values.volume = info["volume"].to_str()
        values.url = info["ee"].to_str() if info["access"].to_str() == "open" else None
        values.year = info["year"].to_str()
        return values

    fields = {
        FieldNames.AUTHOR,
        FieldNames.DOI,
        FieldNames.PAGES,
        FieldNames.TITLE,
        FieldNames.VOLUME,
        FieldNames.URL,
        FieldNames.YEAR,
    }
