"""
Lookup info from https://dblp.org
"""

from typing import Dict, Iterable, List

from ..bibtex.author import Author
from ..bibtex.constants import FieldNames
from ..bibtex.entry import BibtexEntry
from ..lookups.lookups import JSON_Lookup
from ..utils.constants import QUERY_MAX_RESULTS
from ..utils.safe_json import SafeJSON


class DBLPLookup(JSON_Lookup):
    """Lookup for info on https://dblp.org
    Uses the API documented here:
    https://dblp.org/faq/13501473.html

    example URLs:
    no DOI mode.
    Author+title mode:
    https://dblp.org/search/publ/api?format=json&h=3&q=Lamiraux+Reactive+Path+Deformation+for+Nonholonomic+Mobile+Robots
    """

    name = "dblp"

    # ============= Performing Queries =====================

    query_doi: bool = False

    domain = "dblp.org"
    path = "/search/publ/api"

    def get_params(self) -> Dict[str, str]:
        search = ""
        if self.authors is not None:
            search += " ".join(self.authors) + " "
        if self.title is not None:
            search += self.title + " "
        return {"format": "json", "h": str(QUERY_MAX_RESULTS), "q": search.strip()}

    # ============= Parsing results into entries =====================

    def get_results(self, data: bytes) -> Iterable[SafeJSON]:
        """Return the result list"""
        return SafeJSON.from_bytes(data)["result"]["hits"]["hit"].iter_list()

    @staticmethod
    def get_authors(info: SafeJSON) -> List[Author]:
        """Return a bibtex formatted list of authors"""
        authors = info["authors"]["author"]
        formatted = []
        for author in authors.iter_list():
            name = author["text"].to_str()
            if name is None:
                continue
            name = name.strip()
            # Some DBLP authors have a 4-digit disambiguation number
            # Added to their names..., ex : "Ralf Jung 0002"
            if len(name) > 4 and name[-4:].isnumeric():
                name = name[:-4].strip()
            aut = Author.from_name(name)
            if aut is not None:
                formatted.append(aut)
        return formatted

    def get_value(self, result: SafeJSON) -> BibtexEntry:
        info = result["info"]
        values = BibtexEntry(self.name, self.entry.id)
        values.author.set(self.get_authors(info))
        values.doi.set(info["doi"].to_str())
        values.pages.set_str(info["pages"].to_str())
        values.title.set(info["title"].to_str())
        values.volume.set(info["volume"].to_str())
        values.url.set(info["ee"].to_str() if info["access"].to_str() == "open" else None)
        values.year.set(info["year"].to_str())
        return values

    # Set of fields we can get from a query.
    # If all are already present on an entry, the query can be skipped.
    fields = {
        FieldNames.AUTHOR,
        FieldNames.DOI,
        FieldNames.PAGES,
        FieldNames.TITLE,
        FieldNames.VOLUME,
        FieldNames.URL,
        FieldNames.YEAR,
    }
