"""
Lookup info from https://unpaywall.org/
"""

from typing import Dict, Iterable, List, Optional

from ..bibtex.author import Author
from ..bibtex.constants import FieldNames
from ..bibtex.entry import BibtexEntry
from ..lookups.lookups import JSON_Lookup
from ..utils.constants import EMAIL
from ..utils.functions import split_iso_date
from ..utils.safe_json import SafeJSON


class UnpaywallLookup(JSON_Lookup):
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

    # ============= Performing Queries =====================

    query_author_title: bool = False

    domain = "api.unpaywall.org"
    path = "/v2/"

    params = {"email": EMAIL}

    doi: Optional[str] = None
    title: Optional[str] = None

    def get_params(self) -> Dict[str, str]:
        base = dict()
        base.update(super().get_params())
        if self.doi is None:
            if self.title is None:
                raise ValueError("query with no title or doi")
            base["query"] = self.title
        return base

    def get_base_path(self) -> str:
        base = self.path
        if self.doi is not None:
            return base + self.doi
        return base + "search/"

    def get_no_warning_codes(self) -> List[int]:
        """Ignore 404 returned on invalid DOIs"""
        codes = []
        codes.extend(super().get_no_warning_codes())
        if self.doi is not None:
            codes.append(404)
        return codes

    # ============= Parsing results into entries =====================

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
        month = None
        year = None
        if date is not None:
            year, month = split_iso_date(date)
            if month is not None and date[4:] == "-01-01" and len(date) >= 7:
                month = None
        if year is None:
            year = result["year"].force_str()

        title = result["journal_name"].to_str()
        is_journal = result["genre"].to_str() == "journal-article"

        values = BibtexEntry(self.name, self.entry.id)

        values.author.set(self.get_authors(result["z_authors"]))
        values.booktitle.set(None if is_journal else title)
        values.doi.set(result["doi"].to_str())
        values.issn.set_str(result["journal_issn_l"].to_str())
        values.journal.set(title if is_journal else None)
        values.month.set(month)
        values.publisher.set(result["publisher"].to_str())
        values.title.set(result["title"].to_str())
        values.url.set(result["best_oa_location"]["url_for_pdf"].to_str())
        values.year.set(year)

        return values

    # Set of fields we can get from a query.
    # If all are already present on an entry, the query can be skipped.
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
