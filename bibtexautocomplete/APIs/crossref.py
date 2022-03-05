"""
Lookup info from https://www.crossref.org
"""

from typing import Iterable, Optional

from ..bibtex.author import Author
from ..bibtex.entry import BibtexEntry, FieldNames
from ..lookups.lookups import JSON_DAT_Lookup
from ..utils.safe_json import SafeJSON


class CrossrefLookup(JSON_DAT_Lookup):
    """Lookup info on https://www.crossref.org
    Uses the crossref REST API, documentated here:
    https://api.crossref.org/swagger-ui/index.html

    example URLs:
    DOI mode:
    https://api.crossref.org/works/10.1109/tro.2004.829459
    Author + title:
    https://api.crossref.org/works?rows=3&query.title=Reactive+Path+Deformation+for+Nonholonomic+Mobile+Robots&query.author=Lamiraux
    """

    name = "crossref"

    domain = "api.crossref.org"
    path = "/works"

    def get_path(self) -> str:
        if self.doi is not None:
            return self.path + "/" + self.doi
        return super().get_path()

    def get_params(self) -> dict[str, str]:
        base = {"rows": "3"}
        if self.title is not None:
            base["query.title"] = self.title
        if self.author is not None:
            base["query.author"] = self.author
        return base

    def get_results(self, data) -> Optional[Iterable[SafeJSON]]:
        """Return the result list"""
        json = SafeJSON.from_bytes(data)
        if json["status"].to_str() == "ok":
            message = json["message"]
            if self.doi is not None:
                return [message]
            return message["items"].iter_list()
        return None

    def get_title(self, result: SafeJSON) -> Optional[str]:
        """Get the title of a result"""
        return result["title"][0].to_str()

    def get_doi(self, result: SafeJSON) -> Optional[str]:
        """Get the DOI of a result"""
        return result["DOI"].to_str()

    @staticmethod
    def get_authors(authors: SafeJSON) -> list[Author]:
        """Parses JSON output into bibtex formatted author list"""
        formatted = []
        for author in authors.iter_list():
            if not isinstance(author, dict):
                continue
            lastname = author["family"].to_str()
            if lastname is not None:
                formatted.append(Author(lastname, author["given"].to_str()))
        return formatted

    @staticmethod
    def get_date(result: SafeJSON) -> tuple[Optional[str], Optional[str]]:
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
        values = BibtexEntry()
        values.author = self.get_authors(result["author"])
        values.booktitle = result["container-title"][0].to_str()
        values.doi = self.get_doi(result)
        values.issn = result["ISSN"][0].to_str()
        values.isbn = result["ISBN"][0].to_str()
        values.month = month
        values.pages = result["page"].to_str()
        values.publisher = result["publisher"].to_str()
        values.title = self.get_title(result)
        values.volume = result["volume"].to_str()
        values.year = year
        return values

    fields = {
        FieldNames.AUTHOR,
        FieldNames.BOOKTITLE,
        FieldNames.DOI,
        FieldNames.ISSN,
        FieldNames.ISBN,
        FieldNames.MONTH,
        FieldNames.PAGES,
        FieldNames.PUBLISHER,
        FieldNames.TITLE,
        FieldNames.VOLUME,
        FieldNames.YEAR,
    }