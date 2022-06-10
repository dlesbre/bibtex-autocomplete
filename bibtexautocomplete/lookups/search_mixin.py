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
from ..bibtex.matching import ENTRY_CERTAIN_MATCH, ENTRY_NO_MATCH, match_score
from ..utils.logger import logger
from .abstract_base import AbstractEntryLookup

result = TypeVar("result")


class SearchResultMixin(Generic[result]):
    """Iterates through multiple results until a matching one is found

    Defines:
    - process_data : bytes -> Optional[BibtexEntry]

    Virtual methods defined here:
    - get_results : bytes -> Optional[Iterable[result]]
        process data into a list of results
    - get_value : result -> Optional[BibtexEntry] - builds value from a result
    - match_score : entry -> result -> int - matching score
        between the entry and our search term
        value between ENTRY_NO_MATCH and ENTRY_CERTAIN_MATCH (included)
    """

    def get_results(self, data: bytes) -> Optional[Iterable[result]]:
        """Parse the data into a list of results to check
        Return None if no results/invalid data"""
        raise NotImplementedError("should be overridden in child class")

    def get_value(self, res: result) -> BibtexEntry:
        """Return the relevant value (e.g. updated entry)"""
        raise NotImplementedError("should be overridden in child class")

    def match_score(self, entry: BibtexEntry, res: result) -> int:
        """
        Assign a score between ENTRY_NO_MATCH and ENTRY_CERTAIN_MATCH (included)
        representing how likely the given entries matches our search term
        - entry:BibtexEntry is self.get_value(res)
        - res:result is also passed in case get_value forgets some data.
        """
        raise NotImplementedError("should be overridden in child class")
        return match_score(self.entry, entry)

    def process_data(self, data: bytes) -> Optional[BibtexEntry]:
        """Iterate through results until one matches"""
        results = self.get_results(data)
        if results is None:
            logger.verbose_debug("no results")
            return None
        max_score = ENTRY_NO_MATCH
        max_entry: Optional[BibtexEntry] = None
        for res in results:
            entry = self.get_value(res)
            score = self.match_score(entry, res)
            logger.verbose_debug("match {} for {}", score, entry._entry)
            if score >= ENTRY_CERTAIN_MATCH:
                return entry
            if score > max_score:
                max_score = score
                max_entry = entry
        return max_entry


class EntryMatchSearchMixin(SearchResultMixin[result], AbstractEntryLookup):
    """Uses the bibtex entry matcher to get match score"""

    def match_score(self, entry: BibtexEntry, _res: result) -> int:
        return match_score(self.entry, entry)
