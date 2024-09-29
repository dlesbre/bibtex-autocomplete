"""
Lookup info from https://www.crossref.org
"""

from typing import Dict, Iterable, List, Optional, Tuple

from ..bibtex.author import Author
from ..bibtex.constants import FieldNames
from ..bibtex.entry import BibtexEntry
from ..lookups.lookups import JSON_Lookup
from ..utils.constants import QUERY_MAX_RESULTS
from ..utils.safe_json import SafeJSON


class CrossrefLookup(JSON_Lookup):
    """Lookup info on https://www.crossref.org
    Uses the crossref REST API, documented here:
    https://api.crossref.org/swagger-ui/index.html

    example URLs:
    DOI mode:
    https://api.crossref.org/works/10.1109/tro.2004.829459
    Author + title:
    https://api.crossref.org/works?rows=3&query.title=Reactive+Path+Deformation+for+Nonholonomic+Mobile+Robots&query.author=Lamiraux
    """

    name = "crossref"

    # ============= Performing Queries =====================

    domain = "api.crossref.org"
    path = "/works"

    def get_path(self) -> str:
        if self.doi is not None:
            return self.path + "/" + self.doi
        return super().get_path()

    def get_params(self) -> Dict[str, str]:
        base = {"rows": str(QUERY_MAX_RESULTS)}
        if self.title is not None:
            base["query.title"] = self.title
        if self.authors is not None:
            base["query.author"] = " ".join(self.authors)
        return base

    def update_rate_cap(self) -> Optional[float]:
        if self.response is None:
            return None
        limit = self.response.getheader("X-Rate-Limit-Limit")
        interval = self.response.getheader("X-Rate-Limit-Interval")
        if limit is None or interval is None:
            return None
        try:
            return float(interval[:-1]) / float(limit)
        except (ValueError, ZeroDivisionError):
            return None

    def get_no_warning_codes(self) -> List[int]:
        """Ignore 404 returned on invalid DOIs"""
        codes = []
        codes.extend(super().get_no_warning_codes())
        if self.doi is not None:
            codes.append(404)
        return codes

    # ============= Parsing results into entries =====================

    def get_results(self, data: bytes) -> Optional[Iterable[SafeJSON]]:
        """Return the result list"""
        json = SafeJSON.from_bytes(data)
        if json["status"].to_str() == "ok":
            message = json["message"]
            if self.doi is not None:
                return [message]
            return message["items"].iter_list()
        return None

    @staticmethod
    def get_authors(authors: SafeJSON) -> List[Author]:
        """Parses JSON output into bibtex formatted author list"""
        formatted = []
        for author in authors.iter_list():
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
        title = result["container-title"][0].to_str()
        is_journal = result["type"].to_str() == "journal-article"

        values = BibtexEntry(self.name, self.entry.id)

        values.author.set(self.get_authors(result["author"]))
        values.booktitle.set(None if is_journal else title)
        values.doi.set(result["DOI"].to_str())
        values.issn.set_str(result["ISSN"][0].to_str())
        values.isbn.set(result["ISBN"][0].to_str())
        values.journal.set(title if is_journal else None)
        values.month.set(month)
        values.pages.set_str(result["page"].to_str())
        values.publisher.set(result["publisher"].to_str())
        values.title.set(result["title"][0].to_str())
        values.volume.set(result["volume"].to_str())
        values.year.set(year)

        return values

    # Set of fields we can get from a query.
    # If all are already present on an entry, the query can be skipped.
    fields = {
        FieldNames.AUTHOR,
        FieldNames.BOOKTITLE,
        FieldNames.DOI,
        FieldNames.ISSN,
        FieldNames.ISBN,
        FieldNames.JOURNAL,
        FieldNames.MONTH,
        FieldNames.PAGES,
        FieldNames.PUBLISHER,
        FieldNames.TITLE,
        FieldNames.VOLUME,
        FieldNames.YEAR,
    }
