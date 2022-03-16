"""
Bibtexautocomplete
main class used to manage calls to different lookups
"""

from functools import reduce
from pathlib import Path
from threading import Condition
from typing import Container, Iterable, Iterator, List, Optional

from alive_progress import alive_bar  # type: ignore
from bibtexparser.bibdatabase import BibDatabase

from ..bibtex.entry import BibtexEntry
from ..bibtex.io import file_read, file_write, get_entries
from ..bibtex.normalize import has_field
from ..lookups.abstract_base import LookupType
from ..utils.constants import EntryType
from ..utils.logger import PROGRESS, logger
from .threads import LookupThread


class BibtexAutocomplete(Iterable[EntryType]):
    """Main class used to dispatch calls to the relevant lookups"""

    bibdatabases: List[BibDatabase]
    lookups: List[LookupType]
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
        self.lookups = list(lookups)
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

    def autocomplete(self, no_progressbar=False) -> None:
        """Main function that does all the work
        Iterate through entries, performing all lookups"""
        total = self.count_entries() * len(self.lookups)
        entries = list(self)
        condition = Condition()
        threads: list[LookupThread] = []
        with alive_bar(
            total,
            title="Querying databases:",
            disable=no_progressbar,
            enrich_print=False,
            receipt_text=True,
        ) as bar:
            # Create all threads
            for lookup in self.lookups:
                threads.append(LookupThread(lookup, entries, condition, bar))
            condition.acquire()
            # Start all threads
            for thread in threads:
                thread.start()
            position = 0
            while position < self.count_entries():
                # Check if all threads have resolved the current entry
                for thread in threads:
                    if position >= thread.position:
                        # if not wait - release and reaquires lock
                        condition.wait()
                        break
                else:
                    # else update entry with the results
                    changed_fields = 0
                    for thread in threads:
                        result = thread.result[position]
                        if result is not None:
                            changed_fields += self.combine(entries[position], result)
                    if changed_fields != 0:
                        self.changed_entries += 1
                        self.changed_fields += changed_fields
                    bar.text = f"found {self.changed_fields} new fields"
                    position += 1
        logger.log(
            PROGRESS,
            f"Modified {self.changed_entries} / {self.count_entries()} entries"
            f", added {self.changed_fields} fields",
        )

    def combine(self, entry: EntryType, new_info: BibtexEntry) -> int:
        """Adds the information in info to entry.
        Does not overwrite unless self.force_overwrite is True
        only acts on fields contained in self.fields"""
        changed = 0
        for field, value in new_info:
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

    def write(self, files: List[Path]) -> None:
        """Writes the databases in self to the given files
        If not enough files, extra databases are written to stdout
        If too many files, extras are ignored"""
        length = len(files)
        total = len(self.bibdatabases)
        wrote = 0
        for i, db in enumerate(self.bibdatabases):
            file = files[i] if i < length else None
            pretty_file = file if file is not None else "<stdout>"
            logger.debug(f"Writing database {i+1} / {total} to '{pretty_file}'")
            wrote += file_write(file, db)
        logger.log(PROGRESS, f"Wrote {wrote} databases")

    @staticmethod
    def read(files: List[Path]) -> List[BibDatabase]:
        length = len(files)
        dbs = []
        for i, file in enumerate(files):
            logger.debug(f"Reading database {i+1} / {length} from '{file}'")
            dbs.append(file_read(file))
        nb_entries = sum(len(get_entries(db)) for db in dbs)
        logger.log(PROGRESS, f"Read {length} databases, {nb_entries} entries")
        return dbs
