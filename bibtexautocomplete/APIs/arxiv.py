"""
Lookup info from https://arxiv.org
"""

from re import sub
from typing import Dict, Iterable, List, Optional, Tuple
from xml.etree.ElementTree import Element, ParseError, fromstring

from ..bibtex.author import Author
from ..bibtex.constants import FieldNames
from ..bibtex.entry import BibtexEntry
from ..lookups.lookups import XML_Lookup
from ..utils.constants import QUERY_MAX_RESULTS
from ..utils.functions import split_iso_date


class ArxivLookup(XML_Lookup):
    """Lookup info on https://arxiv.org
    Uses the arXiv REST API, documented here:
    https://arxiv.org/help/api/user-manual

    example URLs:
    https://export.arxiv.org/api/query?search_query=Reactive+Path+Deformation+for+Nonholonomic+Mobile+Robots&start=0&max_results=3
    """

    name = "arxiv"

    # ============= Performing Queries =====================

    query_author_title: bool = False
    query_doi: bool = False

    domain = "export.arxiv.org"
    path = "/api/query"
    accept = "application/xml"

    safe = ":"

    query_delay = 3.0  # seconds

    xml_prefix = "{http://www.w3.org/2005/Atom}"

    def get_params(self) -> Dict[str, str]:
        if self.title is None:
            raise ValueError("arXiv called with no title")
        return {
            "search_query": f'ti:"{self.title}"',
            "start": "0",
            "max_results": str(QUERY_MAX_RESULTS),
        }

    # ============= Parsing results into entries =====================

    def get_results(self, data: bytes) -> Optional[Iterable[Element]]:
        """Return the result list"""
        try:
            xml = fromstring(data.decode())
        except ParseError:
            return None
        return xml.findall(self.xml_prefix + "entry")

    def xml_gettext(self, elem: Element, attr: str) -> Optional[str]:
        value = elem.find(self.xml_prefix + attr)
        if value is None:
            return None
        return value.text

    def get_title(self, elem: Element) -> Optional[str]:
        title = self.xml_gettext(elem, "title")
        if title is not None:
            return sub(r"\s+", " ", title)
        return None

    def get_doi(self, elem: Element) -> Optional[str]:
        """Tries to find DOI"""
        for doi in elem.findall("{http://arxiv.org/schemas/atom}doi"):
            if doi.text:
                return doi.text
        for link in elem.findall("{http://www.w3.org/2005/Atom}link"):
            if link.attrib.get("title") == "doi" and link.text:
                return link.text
        return None

    def get_authors(self, elem: Element) -> List[Author]:
        authors = elem.findall(self.xml_prefix + "author")
        formatted = []
        for author in authors:
            name = Author.from_name(self.xml_gettext(author, "name"))
            if name is not None:
                formatted.append(name)
        return formatted

    def get_date(self, elem: Element) -> Tuple[Optional[str], Optional[str]]:
        date = self.xml_gettext(elem, "published")
        year: Optional[str] = None
        month: Optional[str] = None
        if isinstance(date, str):
            year, month = split_iso_date(date)
        return year, month

    def get_link(self, elem: Element) -> Optional[str]:
        for link in elem.findall("{http://www.w3.org/2005/Atom}link"):
            if link.attrib.get("title") == "pdf" and link.text:
                return link.text
        return None

    def get_value(self, result: Element) -> BibtexEntry:
        """Extract bibtex data from JSON output"""
        year, month = self.get_date(result)
        values = BibtexEntry(self.name)
        values.author.set(self.get_authors(result))
        values.doi.set(self.get_doi(result))
        values.month.set(month)
        values.title.set(self.get_title(result))
        values.url.set(self.get_link(result))
        values.year.set(year)
        return values

    # Set of fields we can get from a query.
    # If all are already present on an entry, the query can be skipped.
    fields = {
        FieldNames.AUTHOR,
        FieldNames.DOI,
        FieldNames.MONTH,
        FieldNames.TITLE,
        FieldNames.URL,
        FieldNames.YEAR,
    }
