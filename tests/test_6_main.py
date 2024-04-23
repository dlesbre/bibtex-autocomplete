from typing import Iterable, Optional

from bibtexautocomplete.bibtex.entry import BibtexEntry
from bibtexautocomplete.core.apis import LOOKUPS
from bibtexautocomplete.lookups.abstract_base import AbstractDataLookup, Data
from bibtexautocomplete.lookups.search_mixin import EntryMatchSearchMixin
from bibtexautocomplete.utils.safe_json import SafeJSON


class FakeLookup(EntryMatchSearchMixin[SafeJSON], AbstractDataLookup[BibtexEntry, BibtexEntry]):
    """A fake lookup, complete entries with deterministic info
    Used in test to avoid needlessly querying APIs"""

    name = "fake_lookup"

    def get_data(self) -> Optional[Data]:
        pass

    def get_results(self, data: bytes) -> Optional[Iterable[SafeJSON]]:
        """Parse the data into a list of results to check
        Return None if no results/invalid data"""
        raise NotImplementedError("should be overridden in child class")

    def get_value(self, res: SafeJSON) -> BibtexEntry:
        """Return the relevant value (e.g. updated entry)"""
        raise NotImplementedError("should be overridden in child class")


LOOKUPS.clear()
LOOKUPS.append(FakeLookup)
