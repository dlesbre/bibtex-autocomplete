"""
Lookup info from https://researchr.org/
"""

from typing import Iterable, List
from urllib.parse import quote_plus

from ..bibtex.author import Author
from ..bibtex.entry import BibtexEntry, FieldNames
from ..lookups.lookups import JSON_AT_Lookup
from ..utils.safe_json import SafeJSON


class ResearchrLookup(JSON_AT_Lookup):
    """Lookup for info on https://researchr.org/
    Uses the API documented here:
    https://researchr.org/about/api

    Example urls:
    No doi mode.
    Author title mode:
    https://researchr.org/api/search/publication/Lamiraux+Reactive+Path+Deformation+for+Nonholonomic+Mobile+Robots
    """

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
        values.address = result["address"].to_str()
        values.author = self.get_authors(result["authors"])
        values.booktitle = result["booktitle"].to_str()
        values.doi = result["doi"].to_str()
        values.editor = self.get_authors(result["editors"])
        values.month = result["month"].to_str()
        values.number = result["number"].to_str()
        values.organization = result["organization"].to_str()
        values.pages = (
            f"{page_1}-{page_n}" if page_1 is not None and page_n is not None else None
        )
        values.publisher = result["publisher"].to_str()
        values.title = result["title"].to_str()
        values.volume = result["volume"].to_str()
        values.year = result["year"].to_str()
        return values

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
