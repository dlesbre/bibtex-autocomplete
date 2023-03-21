"""
Lookup info from https://www.semanticscholar.org/
"""
from typing import Dict, Iterable, List, Optional, Tuple

from ..bibtex.author import Author
from ..bibtex.entry import BibtexEntry, FieldNames
from ..lookups.lookups import JSON_DT_Lookup
from ..utils.constants import QUERY_MAX_RESULTS
from ..utils.safe_json import SafeJSON


class SemanticScholarLookup(JSON_DT_Lookup):
    """Lookup info on https://www.semanticscholar.org/
    Uses the crossref REST API, documented here:
    https://api.semanticscholar.org/api-docs/

    example URLs:
    DOI mode:
    https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/tro.2004.829459?fields=paperId%2CexternalIds%2Curl%2Ctitle%2Cvenue%2Cyear%2CisOpenAccess%2CopenAccessPdf%2CfieldsOfStudy%2Cs2FieldsOfStudy%2CpublicationVenue%2CpublicationTypes%2CpublicationDate%2Cjournal%2Cauthors
    Author + title:
    https://api.semanticscholar.org/graph/v1/paper/search?fields=paperId%2CexternalIds%2Curl%2Ctitle%2Cvenue%2Cyear%2CopenAccessPdf%2CpublicationVenue%2CpublicationTypes%2CpublicationDate%2Cjournal%2Cauthors&limit=10&query=Reactive+Path+Deformation+for+Nonholonomic+Mobile+Robots
    """

    # List of field names requested on search, case sensitive
    FIELDS = [
        "paperId",  # Always included
        "externalIds",
        "url",
        "title",  # Included if no fields are specified
        # "abstract",
        "venue",
        "year",
        # "referenceCount",
        # "citationCount",
        # "influentialCitationCount",
        # "isOpenAccess",
        "openAccessPdf",
        # "fieldsOfStudy",
        # "s2FieldsOfStudy",
        "publicationVenue",  # publication venue meta-data for the paper
        "publicationTypes",  # Journal Article, Conference, Review, etc.
        "publicationDate",  # YYYY-MM-DD, if available
        "journal",  # Journal name, volume, and pages, if available
        # "citationStyles",  # Generates bibliographical citation of paper. Currently supported styles: BibTeX
        "authors",
        # "citations", # Up to 1000 will be returned
        # "references", # Up to 1000 will be returned
        # "embedding", # Vector embedding of paper content from the SPECTER model
        # "tldr", # Auto-generated short summary of the paper from the SciTLDR model
    ]

    name = "s2"

    domain = "api.semanticscholar.org"
    path = "/graph/v1/paper"

    def get_base_path(self) -> str:
        if self.doi is not None:
            return self.path + "/DOI:" + self.doi
        return self.path + "/search"

    def get_params(self) -> Dict[str, str]:
        base = {"fields": ",".join(self.FIELDS)}
        if self.doi is not None:
            return base
        if self.title is not None:
            base["limit"] = str(QUERY_MAX_RESULTS)
            base["query"] = self.title
            return base
        return base

    def get_results(self, data: bytes) -> Optional[Iterable[SafeJSON]]:
        """Return the result list"""
        json = SafeJSON.from_bytes(data)
        if self.doi is not None:
            return [json]
        return json["data"].iter_list()

    @staticmethod
    def get_authors(authors: SafeJSON) -> List[Author]:
        """Parses JSON output into bibtex formatted author list"""
        formatted = []
        for author in authors.iter_list():
            autho = Author.from_name(author["name"].to_str())
            if autho is not None:
                formatted.append(autho)
        return formatted

    @staticmethod
    def get_date(result: SafeJSON) -> Tuple[Optional[str], Optional[str]]:
        year = None
        month = None
        pub_date = result["publicationDate"].to_str()
        # date format should be YYYY-MM-DD
        if pub_date is not None:
            if len(pub_date) >= 4 and pub_date[:4].isnumeric():
                year = pub_date[:4]
            if len(pub_date) >= 7 and pub_date[5:7].isnumeric():
                month = pub_date[5:7]
        if year is None:
            year = result["year"].to_str()
        return year, month

    def get_value(self, result: SafeJSON) -> BibtexEntry:
        """Extract bibtex data from JSON output"""
        year, month = self.get_date(result)

        # prefer open access PDF url, else return semantic scholar url
        url = result["openAccessPdf"]["url"].to_str()
        if url is None:
            url = result["url"].to_str()

        # Black formatting is VERY ugly without the two variables
        j1 = result["publicationVenue"]["type"].to_str() == "journal"
        j2 = "JournalArticle" in [
            x.to_str() for x in result["publicationTypes"].iter_list()
        ]
        is_journal = j1 or j2

        venue = result["venue"].to_str()
        if venue is None:
            venue = result["publicationVenue"]["name"].to_str()
        if venue is None:
            venue = result["journal"]["name"].to_str()

        values = BibtexEntry()
        values.author = self.get_authors(result["authors"])
        values.booktitle = None if is_journal else venue
        values.doi = result["externalIds"]["DOI"].to_str()
        values.issn = result["publicationVenue"]["issn"].to_str()
        values.journal = venue if is_journal else None
        values.month = month
        values.pages = result["journal"]["pages"].to_str()
        values.title = result["title"].to_str()
        values.url = url
        values.volume = result["journal"]["volume"].to_str()
        values.year = year
        return values

    fields = {
        FieldNames.AUTHOR,
        FieldNames.BOOKTITLE,
        FieldNames.DOI,
        FieldNames.ISSN,
        FieldNames.JOURNAL,
        FieldNames.MONTH,
        FieldNames.PAGES,
        FieldNames.TITLE,
        FieldNames.URL,
        FieldNames.VOLUME,
        FieldNames.YEAR,
    }