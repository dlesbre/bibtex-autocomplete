"""
Lookup info from https://inspirehep.net/
"""
from typing import Dict, Iterable, List, Optional, Tuple

from ..bibtex.author import Author
from ..bibtex.entry import BibtexEntry, FieldNames
from ..lookups.lookups import JSON_DT_Lookup
from ..utils.constants import QUERY_MAX_RESULTS
from ..utils.functions import make_pages, split_iso_date
from ..utils.safe_json import SafeJSON


class InpireHEPLookup(JSON_DT_Lookup):
    """Lookup info on https://inspirehep.net/
    Uses the API, documented here:
    https://github.com/inspirehep/rest-api-doc

    example URLs:
    DOI mode:
    https://inspirehep.net/api/doi/10.1109/tasc.2023.3336272
    Title:
    https://inspirehep.net/api/literature?q=title+Optimizing+Secondary+CLIQ+for+protecting+High-Field+Accelerator+Magnets
    """

    name = "inspire"

    # ============= Performing Queries =====================

    domain = "inspirehep.net"
    path = "/api"

    # Limited to 15 request in a 5s window
    query_delay: float = 5 / 15

    def get_no_warning_codes(self) -> List[int]:
        """Ignore 404 returned on invalid DOIs"""
        codes = []
        codes.extend(super().get_no_warning_codes())
        if self.doi is not None:
            codes.append(404)
        return codes

    def get_base_path(self) -> str:
        if self.doi is not None:
            return self.path + "/doi/" + self.doi
        return self.path + "/literature/"

    def get_params(self) -> Dict[str, str]:
        base = dict()
        base.update(super().get_params())
        if self.doi is not None:
            return base
        if self.title is not None:
            base["q"] = "title " + self.title
            base["size"] = str(QUERY_MAX_RESULTS)
            return base
        return base

    # ============= Parsing results into entries =====================

    def get_results(self, data: bytes) -> Optional[Iterable[SafeJSON]]:
        """Return the result list"""
        json = SafeJSON.from_bytes(data)
        if self.doi is not None:
            return [json]
        return json["hits"]["hits"].iter_list()

    @staticmethod
    def get_authors(authors: SafeJSON) -> List[Author]:
        """Parses JSON output into bibtex formatted author list"""
        formatted = []
        for author in authors.iter_list():
            autho = Author.from_name(author["full_name"].to_str())
            if autho is not None:
                formatted.append(autho)
        return formatted

    @staticmethod
    def get_date(metadata: SafeJSON) -> Tuple[Optional[str], Optional[str]]:
        year = None
        month = None
        date = metadata["earliest_date"].to_str()
        if date is not None:
            year, month = split_iso_date(date)
        if year is None:
            date = metadata["imprints"][0]["date"].to_str()
            if date is not None:
                year, month = split_iso_date(date)
            if year is None:
                year = metadata["publication_info"][0]["year"].force_str()
        return year, month

    def get_value(self, result: SafeJSON) -> BibtexEntry:
        """Extract bibtex data from JSON output"""
        metadata = result["metadata"]
        journal = metadata["publication_info"][0]
        year, month = self.get_date(metadata)

        first_page = journal["page_start"].force_str()
        last_page = journal["page_end"].force_str()
        pages = make_pages(first_page, last_page)

        values = BibtexEntry()
        values.author = self.get_authors(metadata["authors"])
        values.doi = metadata["dois"][0]["value"].to_str()
        values.isbn = metadata["isbns"][0]["value"].force_str()
        values.journal = journal["journal_title"].to_str()
        values.month = month
        values.number = journal["journal_issue"].force_str()
        values.pages = pages
        values.title = metadata["titles"][0]["title"].to_str()
        values.volume = journal["journal_volume"].to_str()
        values.year = year
        return values

    # Set of fields we can get from a query.
    # If all are already present on an entry, the query can be skipped.
    fields = {
        FieldNames.AUTHOR,
        FieldNames.DOI,
        FieldNames.ISBN,
        FieldNames.JOURNAL,
        FieldNames.MONTH,
        FieldNames.NUMBER,
        FieldNames.PAGES,
        FieldNames.TITLE,
        FieldNames.URL,
        FieldNames.VOLUME,
        FieldNames.YEAR,
    }
