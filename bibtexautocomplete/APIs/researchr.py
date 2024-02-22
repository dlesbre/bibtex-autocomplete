"""
Lookup info from https://researchr.org/
"""

from typing import Iterable, List
from urllib.parse import quote_plus

from ..bibtex.author import Author
from ..bibtex.constants import FieldNames
from ..bibtex.entry import BibtexEntry
from ..lookups.lookups import JSON_Lookup
from ..utils.safe_json import SafeJSON


class ResearchrLookup(JSON_Lookup):
    """Lookup for info on https://researchr.org/
    Uses the API documented here:
    https://researchr.org/about/api

    Example urls:
    No doi mode.
    Author title mode:
    https://researchr.org/api/search/publication/Lamiraux+Reactive+Path+Deformation+for+Nonholonomic+Mobile+Robots
    """

    name = "researchr"

    # ============= Performing Queries =====================

    query_doi: bool = False

    domain = "researchr.org"
    path = "/api/search/publication/"

    def get_base_path(self) -> str:
        search = ""
        if self.authors is not None:
            search += " ".join(self.authors) + " "
        if self.title is not None:
            search += self.title + " "
        return self.path + quote_plus(search.strip())

    # ============= Parsing results into entries =====================

    def get_results(self, data: bytes) -> Iterable[SafeJSON]:
        """Return the result list"""
        return SafeJSON.from_bytes(data)["result"].iter_list()

    @staticmethod
    def get_authors(authors: SafeJSON) -> List[Author]:
        """Return a bibtex formatted list of authors"""
        formatted = []
        for author in authors.iter_list():
            name = author["alias"]["name"].to_str()
            if name is None:
                continue
            name = name.strip()
            # Some authors have a 4-digit disambiguation number
            # Added to their names..., ex : "Peter Müller 0001"
            if len(name) > 4 and name[-4:].isnumeric():
                name = name[:-4].strip()
            aut = Author.from_name(name)
            if aut is not None:
                formatted.append(aut)
        return formatted

    def get_value(self, result: SafeJSON) -> BibtexEntry:
        page_1 = result["firstpage"].to_str()
        page_n = result["lastpage"].to_str()
        values = BibtexEntry(self.name, self.entry.id)
        values.address.set(result["address"].to_str())
        values.author.set(self.get_authors(result["authors"]))
        values.booktitle.set(result["booktitle"].to_str())
        values.doi.set(result["doi"].to_str())
        values.editor.set(self.get_authors(result["editors"]))
        values.month.set(result["month"].to_str())
        values.number.set(result["number"].to_str())
        values.organization.set(result["organization"].to_str())
        values.pages.from_pair(page_1, page_n)
        values.publisher.set(result["publisher"].to_str())
        values.title.set(result["title"].to_str())
        values.volume.set(result["volume"].to_str())
        values.year.set(result["year"].to_str())
        return values

    # Set of fields we can get from a query.
    # If all are already present on an entry, the query can be skipped.
    fields = {
        FieldNames.ADDRESS,
        FieldNames.AUTHOR,
        FieldNames.BOOKTITLE,
        FieldNames.DOI,
        FieldNames.EDITOR,
        FieldNames.MONTH,
        FieldNames.NUMBER,
        FieldNames.ORGANIZATION,
        FieldNames.PAGES,
        FieldNames.PUBLISHER,
        FieldNames.TITLE,
        FieldNames.VOLUME,
        FieldNames.YEAR,
    }
