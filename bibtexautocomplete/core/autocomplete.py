"""
Bibtexautocomplete
main class used to manage calls to different lookups
"""

from datetime import datetime
from functools import reduce
from json import dump as json_dump
from pathlib import Path
from threading import Condition
from typing import (
    Any,
    Callable,
    Container,
    Iterable,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    TypeVar,
    cast,
)

from alive_progress import alive_bar  # type: ignore
from bibtexparser.bibdatabase import BibDatabase

from ..bibtex.base_field import BibtexField
from ..bibtex.constants import FIELD_NO_MATCH, FieldType
from ..bibtex.entry import BibtexEntry
from ..bibtex.io import file_read, file_write, get_entries
from ..bibtex.normalize import has_field
from ..lookups.abstract_entry_lookup import LookupType
from ..utils.constants import (
    BULLET,
    FIELD_PREFIX,
    MARKED_FIELD,
    MAX_THREAD_NB,
    EntryType,
)
from ..utils.logger import VERBOSE_INFO, logger
from ..utils.only_exclude import OnlyExclude
from .data_dump import DataDump
from .threads import LookupThread

T = TypeVar("T")
Q = TypeVar("Q")


def memoize(method: Callable[[T], Q]) -> Callable[[T], Q]:
    """Simple decorator for no argument method memoization
    as an attribute"""
    attribute = "_memoize_" + method.__name__

    def new_method(self: T) -> Q:
        if not hasattr(self, attribute):
            setattr(self, attribute, method(self))
        return cast(Q, getattr(self, attribute))

    return new_method


class Changes(NamedTuple):
    """An atomic change to the bib file"""

    field: str
    new_value: str
    source: str  # Name of one of the lookups


class BibtexAutocomplete(Iterable[EntryType]):
    """Main class used to dispatch calls to the relevant lookups"""

    bibdatabases: List[BibDatabase]
    lookups: List[LookupType]
    fields: Container[str]
    entries: OnlyExclude[str]
    force_overwrite: Container[str]
    force_overwrite_all: bool
    prefix: str
    mark: bool
    filter: Callable[[EntryType], bool]
    dumps: List[DataDump]

    changed_fields: int
    changed_entries: int

    # Ordered list of (entry, changes) where
    # changes is a list of (field, new_value, source)
    changes: List[Tuple[str, List[Changes]]]

    def __init__(
        self,
        bibdatabases: List[BibDatabase],
        lookups: Iterable[LookupType],
        fields: Container[str],
        entries: OnlyExclude[str],
        force_overwrite: Container[str] = [],
        force_overwrite_all: bool = False,
        mark: bool = False,
        ignore_mark: bool = False,
        prefix: bool = False,
    ):
        self.bibdatabases = bibdatabases
        self.lookups = list(lookups)
        self.fields = fields
        self.entries = entries
        self.force_overwrite = force_overwrite
        self.force_overwrite_all = force_overwrite_all
        self.changed_entries = 0
        self.changed_fields = 0
        self.changes = []
        self.dumps = []
        self.prefix = FIELD_PREFIX if prefix else ""
        self.mark = mark
        if ignore_mark:
            self.filter = lambda x: x["ID"] in self.entries
        else:
            self.filter = (
                lambda x: x["ID"] in self.entries and MARKED_FIELD.lower() not in x
            )

    def __iter__(self) -> Iterator[EntryType]:
        """Iterate through entries"""
        for db in self.bibdatabases:
            yield from filter(self.filter, get_entries(db))

    @memoize
    def count_entries(self) -> int:
        """count the number of entries"""
        # Its official, functional programming has infected me...
        return reduce(lambda x, _y: x + 1, self, 0)

    def print_filters(self) -> None:
        """Prints entry filter effects"""
        all_entries = [x["ID"] for db in self.bibdatabases for x in get_entries(db)]
        total = len(all_entries)
        filtered = self.count_entries()
        if total > filtered:
            logger.info("Filtered down to {} entries".format(filtered))
        warn_only, warn_exclude = self.entries.unused(all_entries)
        for x in sorted(warn_only):
            logger.warn('No entry with ID "{ID}"', ID=x)
        for x in sorted(warn_exclude):
            logger.warn('No entry with ID "{ID}"', ID=x)

    @memoize
    def get_id_padding(self) -> int:
        """Return the max length of entries' ID
        to use for pretty printing"""
        max_id_padding = 40
        return min(
            max((len(entry["ID"]) + 1 for entry in self), default=0), max_id_padding
        )

    def autocomplete(self, no_progressbar: bool = False) -> None:
        """Main function that does all the work
        Iterate through entries, performing all lookups"""
        logger.header("Completing entries")
        total = self.count_entries() * len(self.lookups)
        entries = list(self)
        bib_entries: List[BibtexEntry] = []
        for x in entries:
            bib = BibtexEntry("input")
            bib.from_entry(x)
            bib_entries.append(bib)
        condition = Condition()
        assert len(self.lookups) < MAX_THREAD_NB
        threads: List[LookupThread] = []
        with alive_bar(
            total,
            title="Querying databases:",
            disable=no_progressbar,
            enrich_print=False,
            monitor="[{percent:.0%}]",
            monitor_end="[{percent:.0%}]",
            stats="(eta: {eta})",
            stats_end="",
            dual_line=True,
        ) as bar:
            # Create all threads
            for lookup in self.lookups:
                threads.append(LookupThread(lookup, bib_entries, condition, bar))
            condition.acquire()
            # Start all threads
            for thread in threads:
                thread.start()
            position = 0
            nb_entries = self.count_entries()
            while position < nb_entries:
                # Check if all threads have resolved the current entry
                step = True
                thread_positions = []
                for thread in threads:
                    if position >= thread.position:
                        step = False
                    thread_positions.append(f"[{thread.lookup.name}:{thread.position}]")
                bar.text = (
                    " ".join(thread_positions)
                    + f" Found {self.changed_fields} new fields"
                )
                if not step:  # Some threads have not found data for current entry
                    condition.wait()
                else:  # update data for current entry
                    self.update_entry(entries[position], threads, position)
                    position += 1
        logger.info(
            "Modified {changed_entries} / {count_entries} entries"
            ", added {changed_fields} fields",
            changed_entries=self.changed_entries,
            count_entries=self.count_entries(),
            changed_fields=self.changed_fields,
        )

    def update_entry(
        self, entry: EntryType, threads: List[LookupThread], position: int
    ) -> None:
        """Reads all data the threads have found on a new entry,
        and uses it to update the entry with new fields"""
        changes: List[Changes] = []
        results: List[BibtexEntry] = []
        entry_id = entry.get("ID", "<unnamed>")
        new_fields: Set[FieldType] = set()

        dump = DataDump(entry_id)
        for thread in threads:
            result, info = thread.result[position]
            dump.add_entry(thread.lookup.name, result, info)
            if result is not None:
                results.append(result)
                new_fields = new_fields.union(result.fields())

        for field in new_fields:
            # Filter which fields to add
            if not (
                self.force_overwrite_all
                or (field in self.force_overwrite)
                or (not has_field(entry, field))
            ):
                continue
            bib_field = self.combine_field(results, field)
            if bib_field is None:
                continue
            value = bib_field.to_str()
            if value is None:
                continue
            entry[self.prefix + field] = value
            changes.append(Changes(field, value, bib_field.source))

        dump.new_fields = len(changes)
        if changes != []:
            self.changed_entries += 1
            self.changed_fields += len(changes)
            self.changes.append((entry_id, changes))
        logger.verbose_info(
            BULLET + "{StBold}{entry}{StBoldOff} {nb} new fields",
            entry=entry["ID"].ljust(self.get_id_padding()),
            nb=len(changes),
        )
        self.dumps.append(dump)
        if self.mark:
            entry[MARKED_FIELD] = datetime.today().strftime("%Y-%m-%d")

    def combine_field(
        self, results: List[BibtexEntry], fieldname: FieldType
    ) -> Optional[BibtexField[Any]]:
        """Combine the values of a single field"""
        fields = [entry.get_field(fieldname) for entry in results if fieldname in entry]
        groups: List[Tuple[int, BibtexField[Any]]] = []
        for field in fields:
            for i, (count, combined_field) in enumerate(groups):
                score = combined_field.matches(field)
                if score is not None and score > FIELD_NO_MATCH:
                    groups[i] = (count + 1, combined_field.combine(field))
                    break
            else:
                groups.append((1, field))
        # Return the first maximal element that passes the test
        # We use reverse sort to have elements with biggest counts at the front
        # While retaining order on elements with equal counts
        groups.sort(key=lambda x: x[0], reverse=True)
        for _, elt in groups:
            if elt.value is not None and elt.slow_check(elt.value):
                return elt
        return None

    def print_changes(self) -> None:
        """prints a pretty list of changes"""
        logger.header("New fields", VERBOSE_INFO)
        if self.changes == []:
            logger.verbose_info("No new fields")
            return None
        for entry, changes in sorted(self.changes, key=lambda x: x[0]):
            logger.verbose_info(
                BULLET + "{StBold}{entry}{Reset}:",
                entry=entry,
            )
            for field, value, source in changes:
                logger.verbose_info(
                    "    {FgBlue}{field}{Reset}{FgWhite}{StFaint} = {{{Reset}"
                    "{value}{FgWhite}{StFaint}}},{Reset}"
                    " {FgGreen}{StItalics}% {source}{Reset}",
                    field=field,
                    value=value,
                    source=source,
                )

    wrote_header = False

    def write_header(self) -> None:
        """Ensures the final section header is only written once"""
        if not self.wrote_header:
            logger.header("Writing files")
        self.wrote_header = True

    def write_dumps(self, path: Path) -> None:
        """Write the dumps to the given file"""
        self.write_header()
        json = [dump.to_dict() for dump in self.dumps]
        logger.info("Writing data dump to '{}'", str(path))
        try:
            with open(path, "w", encoding="utf-8") as file:
                json_dump(json, file, indent=2)
        except (IOError, UnicodeDecodeError) as err:
            logger.error(
                "Failed to dump data to '{path}' : {FgPurple}{err}{Reset}",
                path=str(path),
                err=err,
            )

    def write(self, files: List[Path]) -> None:
        """Writes the databases in self to the given files
        If not enough files, extra databases are written to stdout
        If too many files, extras are ignored"""
        self.write_header()
        total = len(self.bibdatabases)
        wrote = 0
        for i, db in enumerate(self.bibdatabases):
            file = files[i]
            logger.info(
                "Writing file {id} / {total} to '{file}'",
                id=i + 1,
                total=total,
                file=file,
            )
            wrote += file_write(file, db)
        logger.info(
            "Wrote {total} {files}",
            total=wrote,
            files="file" if wrote == 1 else "files",
        )

    @staticmethod
    def read(files: List[Path]) -> List[BibDatabase]:
        logger.header("Reading files")
        length = len(files)
        dbs = []
        for i, file in enumerate(files):
            logger.info(
                "Reading file {id} / {length} from '{file}'",
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
