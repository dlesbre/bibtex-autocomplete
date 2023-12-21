"""
Lookup info from https://openalex.org/
"""
from typing import Dict, Iterable, List, Optional, Tuple

from ..bibtex.author import Author
from ..bibtex.entry import BibtexEntry, FieldNames
from ..lookups.lookups import JSON_DT_Lookup
from ..utils.constants import QUERY_MAX_RESULTS
from ..utils.functions import make_pages, split_iso_date
from ..utils.safe_json import SafeJSON


class OpenAlexLookup(JSON_DT_Lookup):
    """Lookup info on https://openalex.org/
    Uses the API, documented here:
    https://docs.openalex.org/

    example URLs:
    DOI mode:
    https://api.openalex.org/works/https://doi.org/10.1145/3571258
    Title:
    https://api.openalex.org/works?filter=title.search:SSA%20Translation%20is%20an%20abstract%20Interpretation
    """

    name = "openalex"

    # ============= Performing Queries =====================

    domain = "api.openalex.org"
    path = "/works"

    # Limited to 100_000 requests per day (1.15 request per second)
    # And max 10 queries per second
    query_delay: float = 0.3

    def get_no_warning_codes(self) -> List[int]:
        """Ignore 404 returned on invalid DOIs"""
        codes = []
        codes.extend(super().get_no_warning_codes())
        if self.doi is not None:
            codes.append(404)
        return codes

    def get_base_path(self) -> str:
        if self.doi is not None:
            return self.path + "/https://doi.org/" + self.doi
        return self.path

    def get_params(self) -> Dict[str, str]:
        base = dict()
        base.update(super().get_params())
        if self.doi is not None:
            return base
        if self.title is not None:
            base["filter"] = "title.search:" + self.title
            base["per-page"] = str(QUERY_MAX_RESULTS)
        return base

    # ============= Parsing results into entries =====================

    def get_results(self, data: bytes) -> Optional[Iterable[SafeJSON]]:
        """Return the result list"""
        json = SafeJSON.from_bytes(data)
        if self.doi is not None:
            return [json]
        return json["results"].iter_list()

    @staticmethod
    def get_authors(authors: SafeJSON) -> List[Author]:
        """Parses JSON output into bibtex formatted author list"""
        formatted = []
        for author in authors.iter_list():
            autho = Author.from_name(author["author"]["display_name"].to_str())
            if autho is not None:
                formatted.append(autho)
        return formatted

    @staticmethod
    def get_date(result: SafeJSON) -> Tuple[Optional[str], Optional[str]]:
        year = None
        month = None
        pub_date = result["publication_date"].to_str()
        # date format should be YYYY-MM-DD
        if pub_date is not None:
            year, month = split_iso_date(pub_date)
        if year is None:
            year = str(result["publication_year"].to_int())
        return year, month

    def get_value(self, result: SafeJSON) -> BibtexEntry:
        """Extract bibtex data from JSON output"""
        year, month = self.get_date(result)

        location = result["primary_location"]
        url = result["best_oa_location"]["pdf_url"].to_str()
        if url is None:
            url = result["best_oa_location"]["landing_page_url"].to_str()
        if url is None:
            url = location["pdf_url"].to_str()
        if url is None:
            url = location["landing_page_url"].to_str()

        is_book = result["type"].to_str() in ["book", "book-chapter"]
        journal = location["source"]["display_name"].to_str()

        first_page = result["biblio"]["first_page"].to_str()
        last_page = result["biblio"]["last_page"].to_str()
        pages = make_pages(first_page, last_page)

        values = BibtexEntry()
        values.author = self.get_authors(result["authorships"])
        values.doi = result["doi"].to_str()
        values.issn = location["source"]["issn_l"].to_str()
        values.journal = journal if not is_book else None
        values.month = month
        values.number = result["biblio"]["issue"].to_str()
        values.pages = pages
        values.publisher = location["source"]["host_organization_name"].to_str()
        values.title = result["display_name"].to_str()
        values.url = url
        values.volume = result["biblio"]["volume"].to_str()
        values.year = year
        return values

    # Set of fields we can get from a query.
    # If all are already present on an entry, the query can be skipped.
    fields = {
        FieldNames.AUTHOR,
        FieldNames.DOI,
        FieldNames.ISSN,
        FieldNames.JOURNAL,
        FieldNames.MONTH,
        FieldNames.NUMBER,
        FieldNames.PAGES,
        FieldNames.PUBLISHER,
        FieldNames.TITLE,
        FieldNames.URL,
        FieldNames.VOLUME,
        FieldNames.YEAR,
    }
