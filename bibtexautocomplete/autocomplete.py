from functools import reduce
from typing import Container, Iterable, Iterator, List, Optional

from bibtexparser.bibdatabase import BibDatabase

from .abstractlookup import LookupType, ResultType
from .bibtex import get_entries, has_field, write_to
from .defs import PROGRESS, EntryType, logger


class BibtexAutocomplete(Iterable[EntryType]):
    """Main class used to dispatch calls to the relevant lookups"""

    bibdatabases: List[BibDatabase]
    lookups: Iterable[LookupType]
    fields: Container[str]
    entries: Container[str]
    force_overwrite: bool

    changed_fields: int = 0
    changed_entries: int = 0

    _total_entries: Optional[int] = None

    def __init__(
        self,
        bibdatabases: List[BibDatabase],
        lookups: Iterable[LookupType],
        fields: Container[str],
        entries: Container[str],
        force_overwrite: bool,
    ):
        self.bibdatabases = bibdatabases
        self.lookups = lookups
        self.fields = fields
        self.entries = entries
        self.force_overwrite = force_overwrite

    def __iter__(self) -> Iterator[EntryType]:
        """Iterate through entries"""
        for db in self.bibdatabases:
            for entry in filter(self.entries.__contains__, get_entries(db)):
                yield entry

    def count_entries(self) -> int:
        """count the number of entries"""
        # Its official, functional programming has infected me...
        if self._total_entries is None:
            self._total_entries = reduce(lambda x, _y: x + 1, self, 0)
        return self._total_entries

    def autocomplete(self) -> None:
        """Main function that does all the work
        Iterate through entries, performing all lookups"""
        for entry in self:
            changed_fields = 0
            for lookup in self.lookups:
                init = lookup(entry)
                info = init.query()
                if info is not None:
                    changed_fields += self.combine(entry, info)
            if changed_fields != 0:
                self.changed_entries += 1
                self.changed_fields += changed_fields

    def combine(self, entry: EntryType, new_info: ResultType) -> int:
        """Adds the information in info to entry.
        Does not overwrite unless self.force_overwrite is True
        only acts on fields contained in self.fields"""
        changed = 0
        for field, value in new_info.items():
            if field not in self.fields:
                continue
            # Does the field actually contain any value
            if value is None:
                continue
            svalue = str(value)
            if svalue.strip() == "":
                continue
            # Is it present on entry
            if self.force_overwrite or (not has_field(entry, field)):
                logger.debug(f"{entry['ID']}.{field} := {svalue}")
                changed += 1
                entry[field] = svalue
        return changed

    def write(self, files: List[str]) -> None:
        """Writes the databases in self to the given files
        If not enough files, extra databases are written to stdout
        If too many files, extras are ignored"""
        length = len(files)
        total = len(self.bibdatabases)
        for i, db in enumerate(self.bibdatabases):
            file = files[i] if i < length else None
            pretty_file = file if file is not None else "<stdout>"
            logger.debug(f"Writing database {i} / {total} to {pretty_file}")
            try:
                write_to(file, db)
            except IOError:
                logger.error(f"When writing database {i} / {total} to {pretty_file}")
        logger.log(PROGRESS, f"Wrote {total} databases")

    @staticmethod
    def read():
        pass
