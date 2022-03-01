from typing import Iterator, List

from bibtexparser.bibdatabase import BibDatabase

from .abstractlookup import LookupType
from .bibtex import get_entries, has_field
from .defs import EntryType, logger
from .lookup import CrossrefLookup, DBLPLookup, ResearchrLookup, UnpaywallLookup


def memoize(attr_name: str):
    def decorator(function):
        def helper(self):
            if hasattr(self, attr_name):
                return getattr(self, attr_name)
            value = function(self)
            setattr(self, attr_name, value)
            return value


class BibtexAutocomplete:
    """Main class used to dispatch calls to the relevant lookups"""

    bibdatabases: List[BibDatabase]
    progress_doi: float = 0.0
    progress_url: float = 0.0

    DOI_lookups: List[LookupType] = [
        CrossrefLookup,
        DBLPLookup,
        ResearchrLookup,
        UnpaywallLookup,
    ]

    def iter_lookups(self) -> Iterator[LookupType]:
        """"""

    def iter_entries(self) -> Iterator[EntryType]:
        """Iterate through entries"""
        for db in self.bibdatabases:
            for entry in get_entries(db):
                yield entry
        raise StopIteration()

    @memoize("_total_entries")
    def count_entries(self) -> int:
        """count the number of entries"""
        count = 0
        for db in self.bibdatabases:
            entries = get_entries(db)
            count += len(entries)
        return count

    def autocomplete(self) -> None:
        """Tries to find missing DOIs"""
        found = 0
        for entry in self.iter_entries():
            if has_field(entry, "doi"):
                continue
            for lookup in self.DOI_lookups:
                init = lookup(entry)
                res = init.query()
                if res is not None:
                    logger.info(f"Found DOI for {entry['ID']} : {res}")
                    # entry["doi"] = res
                    found += 1
                    break
