"""
Mixin that override process_data
assuming there are multiple results

New virtual methods:
- get_results : bytes -> Optional[Iterable[result]]
    process data into a list of results
- get_value : result -> BibtexEntry - builds value from a result
"""

from typing import Generic, Iterable, Optional, TypeVar

from ..bibtex.entry import BibtexEntry
from ..bibtex.normalize import normalize_doi, normalize_str
from ..utils.logger import logger
from .abstract_base import AbstractEntryLookup

result = TypeVar("result")


class SearchResultMixin(Generic[result]):
    """Iterates through multiple results until a matching one is found

    Defines:
    - handle_output : bytes -> Optional[BibtexEntry]

    Virtual methods defined here:
    - get_results : bytes -> Optional[Iterable[result]]
        process data into a list of results
    - matches_entry : result -> bool - does the result match self.entry ?
    - get_value : result -> Optional[BibtexEntry] - builds value from a result"""

    def get_results(self, data: bytes) -> Optional[Iterable[result]]:
        """Parse the data into a list of results to check
        Return None if no results/invalid data"""
        raise NotImplementedError("should be overridden in child class")

    def get_value(self, res: result) -> BibtexEntry:
        """Return the relevant value (e.g. updated entry)"""
        raise NotImplementedError("should be overridden in child class")

    def matches_entry(self, res: result) -> bool:
        """Return true if the result matches self.entry
        By default matches titles, can be overridden for different behavior"""
        raise NotImplementedError("should be overridden in child class")

    def process_data(self, data: bytes) -> Optional[BibtexEntry]:
        """Iterate through results until one matches"""
        results = self.get_results(data)
        if results is None:
            logger.debug("no results")
            return None
        for res in results:
            if self.matches_entry(res):
                # We found a match,
                # No need to keep searching or querying this database
                # even if the match is empty
                return self.get_value(res)
        return None


class DOITitleSearchMixin(SearchResultMixin[result], AbstractEntryLookup):
    """matches based on doi (if present on both) or title (with str_similar)

    Virtual methods:
    - get_doi : result -> Optional[str]
    - get_title : result -> Optional[str]"""

    def get_doi(self, res: result) -> Optional[str]:
        """Return the result's DOI if present"""
        raise NotImplementedError("should be overridden in child class")

    def get_title(self, res: result) -> Optional[str]:
        """Return the result's title if present"""
        raise NotImplementedError("should be overridden in child class")

    def matches_entry(self, res: result) -> bool:
        res_doi = normalize_doi(self.get_doi(res))
        ent_doi = self.entry.doi
        if res_doi is not None and ent_doi is not None and res_doi == ent_doi:
            return True
        res_title = self.get_title(res)
        ent_title = self.entry.title
        return (
            res_title is not None
            and ent_title is not None
            and normalize_str(ent_title) == normalize_str(res_title)
        )
