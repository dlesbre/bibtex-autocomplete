"""
Bibtexautocomplete
main class used to manage calls to different lookups
"""

from functools import reduce
from pathlib import Path
from threading import Condition
from typing import Callable, Container, Iterable, Iterator, List, TypeVar

from alive_progress import alive_bar  # type: ignore
from bibtexparser.bibdatabase import BibDatabase

from ..bibtex.entry import BibtexEntry
from ..bibtex.io import file_read, file_write, get_entries
from ..bibtex.normalize import has_field
from ..lookups.abstract_base import LookupType
from ..utils.ansi import ansi_format
from ..utils.constants import MAX_THREAD_NB, EntryType
from ..utils.logger import VERBOSE_INFO, logger
from .threads import LookupThread

T = TypeVar("T")
Q = TypeVar("Q")


def memoize(method: Callable[[T], Q]) -> Callable[[T], Q]:
    """Simple decorator for no argument method memoization
    as an attribute"""
    attribute = "_memoize_" + method.__name__

    def new_method(self):
        if not hasattr(self, attribute):
            setattr(self, attribute, method(self))
        return getattr(self, attribute)

    return new_method


BULLET = "{FgBlue}{StBold}*{StBoldOff}{FgReset} "


class BibtexAutocomplete(Iterable[EntryType]):
    """Main class used to dispatch calls to the relevant lookups"""

    bibdatabases: List[BibDatabase]
    lookups: List[LookupType]
    fields: Container[str]
    entries: Container[str]
    force_overwrite: bool

    changed_fields: int
    changed_entries: int

    # Ordered list of (entry, changes) where
    # changes is a list of (field, new_value)
    changes: list[tuple[str, list[tuple[str, str]]]]

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
        self.changed_entries = 0
        self.changed_fields = 0
        self.changes = []

    def __iter__(self) -> Iterator[EntryType]:
        """Iterate through entries"""
        for db in self.bibdatabases:
            for entry in filter(self.entries.__contains__, get_entries(db)):
                yield entry

    @memoize
    def count_entries(self) -> int:
        """count the number of entries"""
        # Its official, functional programming has infected me...
        return reduce(lambda x, _y: x + 1, self, 0)

    @memoize
    def get_id_padding(self) -> int:
        """Return the max length of entries' ID
        to use for pretty printing"""
        max_id_padding = 40
        return min(
            max((len(entry["ID"]) + 1 for entry in self), default=0), max_id_padding
        )

    def autocomplete(self, no_progressbar=False) -> None:
        """Main function that does all the work
        Iterate through entries, performing all lookups"""
        logger.header("Completing entries")
        total = self.count_entries() * len(self.lookups)
        padding = self.get_id_padding()
        entries = list(self)
        condition = Condition()
        assert len(self.lookups) < MAX_THREAD_NB
        threads: list[LookupThread] = []
        with alive_bar(
            total,
            title=ansi_format("{FgBlue}Querying databases:{FgReset}"),
            disable=no_progressbar,
            enrich_print=False,
            receipt_text=True,
            monitor=ansi_format("[{FgBlue}{{percent:.0%}}{FgReset}]"),
            monitor_end=ansi_format("[ {FgBlue}{{percent:.0%}}{FgReset}]"),
            stats="(eta: {eta})",
            stats_end="",
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
                    entry = entries[position]
                    for thread in threads:
                        result = thread.result[position]
                        if result is not None:
                            changed_fields += self.combine(entry, result)
                    if changed_fields != 0:
                        self.changed_entries += 1
                        self.changed_fields += changed_fields
                    logger.verbose_info(
                        BULLET + "{StBold}{entry}{StBoldOff} {nb} new fields",
                        entry=entry["ID"].ljust(padding),
                        nb=changed_fields,
                    )
                    bar.text = f"found {self.changed_fields} new fields"
                    position += 1
        logger.info(
            "Modified {changed_entries} / {count_entries} entries"
            ", added {changed_fields} fields",
            changed_entries=self.changed_entries,
            count_entries=self.count_entries(),
            changed_fields=self.changed_fields,
        )

    def combine(self, entry: EntryType, new_info: BibtexEntry) -> int:
        """Adds the information in info to entry.
        Does not overwrite unless self.force_overwrite is True
        only acts on fields contained in self.fields"""
        changed = 0
        changes = []
        for field, value in new_info:
            if field not in self.fields:
                continue
            # Does the field actually contain any value
            if value is None:
                continue
            s_value = str(value)
            if s_value.strip() == "":
                continue
            # Is it present on entry
            if self.force_overwrite or (not has_field(entry, field)):
                logger.verbose_debug(
                    "{ID}.{field} := {value}",
                    ID=entry["ID"],
                    field=field,
                    value=s_value,
                )
                changes.append((field, s_value))
                changed += 1
                entry[field] = s_value
        if changed:
            self.changes.append((entry["ID"], changes))
        return changed

    def print_changes(self) -> None:
        """prints a pretty list of changes"""
        logger.header("New fields", VERBOSE_INFO)
        if self.changes == []:
            logger.verbose_info("No new fields")
            return None
        for entry, changes in self.changes:
            logger.verbose_info(
                BULLET + "{StBold}{entry}{StBoldOff}:",
                entry=entry,
            )
            for field, value in changes:
                logger.verbose_info(
                    "    {FgBlue}{field}{FgReset} = {{{value}}},",
                    field=field,
                    value=value,
                )

    def write(self, files: List[Path]) -> None:
        """Writes the databases in self to the given files
        If not enough files, extra databases are written to stdout
        If too many files, extras are ignored"""
        logger.header("Writing files")
        length = len(files)
        total = len(self.bibdatabases)
        wrote = 0
        for i, db in enumerate(self.bibdatabases):
            file = files[i] if i < length else None
            pretty_file = file if file is not None else "<stdout>"
            logger.info(
                "Writing database {id} / {total} to '{file}'",
                id=i + 1,
                total=total,
                file=pretty_file,
            )
            wrote += file_write(file, db)
        logger.info("Wrote {total} databases", total=wrote)

    @staticmethod
    def read(files: List[Path]) -> List[BibDatabase]:
        logger.header("Reading files")
        length = len(files)
        dbs = []
        for i, file in enumerate(files):
            logger.debug(
                "Reading database {id} / {length} from '{file}'",
                id=i + 1,
                length=length,
                file=file,
            )
            dbs.append(file_read(file))
        nb_entries = sum(len(get_entries(db)) for db in dbs)
        logger.info(
            "Read {nb_entries} {entry} from {total} {file}",
            total=length,
            nb_entries=nb_entries,
            entry="entries" if nb_entries != 1 else "entry",
            file="files" if length != 1 else "file",
        )
        return dbs
