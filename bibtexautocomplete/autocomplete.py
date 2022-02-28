from typing import Iterator, List

from bibtexparser.bibdatabase import BibDatabase

from .bibtex import get_entries, has_field
from .constants import EntryType


class BibtexAutocomplete:
    """Main class used to dispatch calls to the relevant lookups"""

    bibdatabases: List[BibDatabase]

    def iter_entries(self) -> Iterator[EntryType]:
        """Iterate through entries"""
        for db in self.bibdatabases:
            for entry in get_entries(db):
                yield entry
        raise StopIteration()

    def count_entries(self) -> int:
        """count the number of entries"""
        count = 0
        for db in self.bibdatabases:
            entries = get_entries(db)
            count += len(entries)
        return count

    def count_missing(self, field: str) -> int:
        """Counts the number of entries missing the given field"""
        count = 0
        for entry in self.iter_entries():
            if not has_field(entry, field):
                count += 1
        return count
