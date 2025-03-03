"""
Bibtexautocomplete
main class used to manage calls to different lookups
"""

from datetime import datetime, timedelta
from fileinput import input
from functools import reduce
from json import dump as json_dump
from logging import INFO
from pathlib import Path
from re import compile, sub
from sys import maxunicode
from threading import Condition
from typing import (
    Any,
    Callable,
    Container,
    Iterable,
    Iterator,
    List,
    Literal,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from alive_progress import alive_bar  # type: ignore
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.latexenc import string_to_latex

from ..bibtex.base_field import BibtexField
from ..bibtex.constants import FIELD_NO_MATCH, FieldType, SearchedFields
from ..bibtex.entry import ENTRY_TYPES, BibtexEntry
from ..bibtex.io import file_read, file_write, get_entries, make_writer, read, write
from ..bibtex.normalize import has_field
from ..lookups.abstract_entry_lookup import LookupType
from ..lookups.https import HTTPSLookup
from ..utils.ansi import ANSICodes
from ..utils.constants import (
    BULLET,
    CONNECTION_TIMEOUT,
    FIELD_PREFIX,
    MARKED_FIELD,
    MAX_THREAD_NB,
    SKIP_QUERIES_IF_DELAY,
    SKIP_QUERIES_IF_REMAINING,
    AuthorType,
    EntryType,
    PathType,
)
from ..utils.logger import VERBOSE_INFO, Hint, logger
from ..utils.only_exclude import OnlyExclude
from .apis import LOOKUPS
from .data_dump import DataDump
from .parser import indent_string
from .threads import LookupThread

T = TypeVar("T")
Q = TypeVar("Q")


UPPER = "".join(chr(i) for i in range(maxunicode) if chr(i).isupper())
LOWER = "".join(chr(i) for i in range(maxunicode) if chr(i).islower())

WORD_WITH_UPPERCASE = compile("([" + LOWER + "]*[" + UPPER + "]+[" + LOWER + UPPER + "]*)")


InterruptHint = Hint(
    "it looks like this may take a while...\n"
    "If needed, BTAC can be safely interrupted with Ctrl+C / SIGINT.\n"
    "When interrupted, all completed and uncompleted entries are written to\n"
    "a new temporary file. You can then resume completion where interrupted\n"
    "using the {FgYellow}--sf / --start-from{Reset} command line option."
)

SkipHint = Hint(
    "Skipping occurs to avoid potentially very long wait times if a few\n"
    "sources are significantly slower to respond. It can be disabled with the\n"
    "{FgYellow}--no-skip{Reset} command line option."
)


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
    fields_to_complete: Set[FieldType]  # Set of fields to complete
    entries: Container[str]
    start_from: Optional[str]
    fields_to_overwrite: Set[FieldType]
    escape_unicode: bool
    fields_to_protect_uppercase: Container[str]
    prefix: str
    mark: bool
    filter: Callable[[EntryType], bool]
    dumps: List[DataDump]
    diff_mode: bool
    copy_doi_to_url: bool
    filter_by_entrytype: Literal["no", "required", "optional", "all"]
    dont_skip_slow_queries: bool
    writer: BibTexWriter

    changed_fields: int
    changed_entries: int

    # Ordered list of (entry, changes) where
    # changes is a list of (field, new_value, source)
    changes: List[Tuple[str, List[Changes]]]

    # Current position when completing entries
    position: int

    def __init__(
        self,
        *,
        lookups: Iterable[LookupType] = LOOKUPS,
        entries: Optional[Container[str]] = None,
        mark: bool = False,
        ignore_mark: bool = False,
        prefix: bool = False,
        escape_unicode: bool = False,
        diff_mode: bool = False,
        # Restrict which fields should be completed
        fields_to_complete: Optional[Set[FieldType]] = None,
        # Restrict which fields should be overwritten
        fields_to_overwrite: Optional[Set[FieldType]] = None,
        # Specify which fields should have uppercase protection
        fields_to_protect_uppercase: Container[str] = set(),
        filter_by_entrytype: Literal["no", "required", "optional", "all"] = "no",
        copy_doi_to_url: bool = False,
        start_from: Optional[str] = None,
        dont_skip_slow_queries: bool = False,
        timeout: Optional[float] = CONNECTION_TIMEOUT,  # Timeout on all queries, in seconds
        ignore_ssl: bool = False,  # Bypass SSL verification
        verbose: int = 0,  # Verbosity level, from 4 (very verbose debug) to -3 (no output)
        # Output formatting
        align_values: bool = False,
        comma_first: bool = False,
        no_trailing_comma: bool = False,
        indent: str = "\t",
        color: Optional[Literal["auto", "always", "never"]] = None,
    ):
        # main set the color directly because it can output various warnings,
        # but for API use, we can also set the color here
        if color is not None:
            ANSICodes.auto_colors(color)
        HTTPSLookup.connection_timeout = timeout if isinstance(timeout, float) and timeout > 0.0 else None
        HTTPSLookup.ignore_ssl = ignore_ssl
        logger.set_verbosity(verbose)

        self.writer = make_writer()
        self.writer.align_values = align_values
        self.writer.comma_first = comma_first
        self.writer.add_trailing_comma = no_trailing_comma
        self.writer.indent = indent_string(indent)

        if fields_to_complete is None:
            fields_to_complete = SearchedFields.copy()
        if fields_to_overwrite is None:
            fields_to_overwrite = set()
        self.bibdatabases = []
        self.lookups = list(lookups)
        self.fields_to_complete = fields_to_complete
        self.entries = OnlyExclude(None, None) if entries is None else entries
        self.fields_to_overwrite = fields_to_complete & fields_to_overwrite
        self.changed_entries = 0
        self.changed_fields = 0
        self.changes = []
        self.dumps = []
        self.prefix = FIELD_PREFIX if prefix else ""
        self.mark = mark
        if ignore_mark:
            self.filter = lambda x: x["ID"] in self.entries
        else:
            self.filter = lambda x: x["ID"] in self.entries and MARKED_FIELD.lower() not in x
        self.escape_unicode = escape_unicode
        self.fields_to_protect_uppercase = fields_to_protect_uppercase
        self.diff_mode = diff_mode
        self.filter_by_entrytype = filter_by_entrytype
        self.position = 0
        self.copy_doi_to_url = copy_doi_to_url
        self.start_from = start_from
        self.dont_skip_slow_queries = dont_skip_slow_queries

    def __iter__(self) -> Iterator[EntryType]:
        """Iterate through entries"""
        has_started = False
        if self.start_from is None:
            has_started = True
        for db in self.bibdatabases:
            for entry in get_entries(db):
                if entry["ID"] == self.start_from:
                    has_started = True
                if has_started and self.filter(entry):
                    yield entry

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
        if isinstance(self.entries, OnlyExclude):
            warn_only, warn_exclude = self.entries.unused(all_entries)
            for x in sorted(warn_only):
                logger.warn('No entry with ID "{ID}"', ID=x)
            for x in sorted(warn_exclude):
                logger.warn('No entry with ID "{ID}"', ID=x)
        if self.start_from is not None and self.start_from not in all_entries:
            logger.critical('--start-from / --sf invalid: no entry with ID "{ID}"', ID=self.start_from)
            raise ValueError("start_from value does not appear in list of entries")

    @memoize
    def get_id_padding(self) -> int:
        """Return the max length of entries' ID to use for pretty printing"""
        max_id_padding = 40
        return min(max((len(entry["ID"]) + 1 for entry in self), default=0), max_id_padding)

    def autocomplete(self, no_progressbar: bool = False) -> None:
        """Main function that does all the work
        Iterate through entries, performing all lookups"""
        logger.header("Completing entries")

        # Some local variables used throughout this function
        nb_entries = self.count_entries()
        assert len(self.lookups) < MAX_THREAD_NB
        is_verbose = logger.get_level() < INFO
        print_hint_time = datetime.now() + timedelta(minutes=5)
        wait_for_threads = True

        # Initialize the set of entries to complete, and the set of missing
        # Fields for each of these
        entries = list(self)
        bib_entries: List[BibtexEntry] = []
        to_complete: List[Set[FieldType]] = []
        for x in entries:
            bib = BibtexEntry.from_entry("input", x)
            bib_entries.append(bib)
            to_complete.append(self.get_fields_to_complete(x))

        # Create all threads
        condition = Condition()
        threads: List[LookupThread] = [
            LookupThread(lookup, bib_entries, to_complete, condition) for lookup in self.lookups
        ]
        condition.acquire()
        for thread in threads:
            thread.start()

        with alive_bar(
            nb_entries,
            title="Querying databases:",
            disable=no_progressbar,
            enrich_print=False,
            monitor="[{percent:.0%}]",
            monitor_end="[{percent:.0%}]",
            stats="(eta: {eta})",
            stats_end="",
            dual_line=True,
        ) as bar:
            self.position = 0
            while self.position < nb_entries:
                # Check if all threads have resolved the current entry
                step = True
                thread_positions = []
                for thread in threads:
                    if self.position >= thread.position:
                        step = False
                    thread_positions.append((thread, thread.position))
                # Update progressbar display
                if is_verbose:
                    bar.text = f"{self.position}/{nb_entries} {self.changed_fields} fields " + " ".join(
                        f"{thread.lookup.name}:{i}" for (thread, i) in thread_positions
                    )
                else:
                    bar.text = f"Processed {self.position}/{nb_entries} entries, found {self.changed_fields} new fields"

                # Check if two thirds of our source have finished
                thread_positions.sort(key=lambda x: x[1])
                two_thirds_pos = thread_positions[len(thread_positions) // 3][1]
                if not self.dont_skip_slow_queries and two_thirds_pos >= nb_entries:
                    # Most source are done, skip the remaining ones if they are
                    # lagging far behind
                    for thread, pos in thread_positions:
                        if pos >= nb_entries:
                            continue
                        remaining = nb_entries - pos
                        # Skip if more than 5 remaining, or a delay of over 120
                        # seconds between querys
                        wait_for_threads = False
                        if remaining >= SKIP_QUERIES_IF_REMAINING or (
                            hasattr(thread.lookup, "query_delay") and thread.lookup.query_delay >= SKIP_QUERIES_IF_DELAY
                        ):
                            thread.skip_to_end = True
                            thread.result += [(None, dict())] * remaining
                            thread.position = nb_entries
                            logger.warn(
                                f"[{{FgBlue}}{thread.name}{{Reset}}] Skipping last {remaining} queries since the"
                                " majority of the other sources have finished."
                            )
                            SkipHint.emit()
                        else:
                            wait_for_threads = True

                # Display a message if the operation will take a while
                if datetime.now() >= print_hint_time and self.position <= nb_entries // 2:
                    InterruptHint.emit()
                if not step:  # Some threads have not found data for current entry
                    if wait_for_threads:
                        condition.wait()
                else:  # update data for current entry
                    bar()
                    self.update_entry(entries[self.position], to_complete[self.position], threads)
                    self.position += 1
        logger.info(
            "Modified {changed_entries} / {count_entries} entries, added {changed_fields} fields",
            changed_entries=self.changed_entries,
            count_entries=nb_entries,
            changed_fields=self.changed_fields,
        )
        # Delete empty entries (in diff mode)
        for db in self.bibdatabases:
            db.entries = list(filter(None, db.entries))

    def get_fields_to_complete_by_entrytype(self, entry: EntryType) -> Set[FieldType]:
        """Set of fields that can be accepted by the current entry,
        Only looking at the given entry type"""
        field_set = self.fields_to_complete.copy()
        if self.filter_by_entrytype == "no":
            return field_set
        entry_type = entry.get("ENTRYTYPE", "misc")
        if entry_type not in ENTRY_TYPES:
            entry_type = "misc"
        entry_fields = ENTRY_TYPES[entry_type]
        if self.filter_by_entrytype == "all":
            return field_set & (entry_fields.required | entry_fields.optional | entry_fields.non_standard)
        if self.filter_by_entrytype == "optional":
            return field_set & (entry_fields.required | entry_fields.optional)
        return field_set & entry_fields.required

    def get_fields_to_complete(self, entry: EntryType) -> Set[FieldType]:
        """Set of fields that can be accepted by the current entry,
        looking at the entrytype and list of present fields"""
        fields = self.get_fields_to_complete_by_entrytype(entry)
        return set(field for field in fields if (not has_field(entry, field)) or field in self.fields_to_overwrite)

    def update_entry(self, entry: EntryType, to_complete: Set[FieldType], threads: List[LookupThread]) -> None:
        """Reads all data the threads have found on a new entry,
        and uses it to update the entry with new fields"""
        changes: List[Changes] = []
        results: List[BibtexEntry] = []
        entry_id = entry.get("ID", "unnamed")
        new_fields: Set[FieldType] = set()

        dump = DataDump(entry_id)
        for thread in threads:
            result, info = thread.result[self.position]
            dump.add_entry(thread.lookup.name, result, info)
            if result is not None:
                result.sanitize(self.copy_doi_to_url)
                results.append(result)
                new_fields = new_fields.union(result.fields())

        new_entry: EntryType = dict()
        for field in new_fields:
            # Filter which fields to add
            if field not in to_complete:
                continue
            bib_field = self.combine_field(results, field, entry_id)
            if bib_field is None:
                continue
            value = bib_field.to_str()
            if value is None:
                continue
            if field in self.fields_to_protect_uppercase:
                value = sub(WORD_WITH_UPPERCASE, "{\\g<1>}", value)
            if self.escape_unicode:
                value = string_to_latex(value)
                assert isinstance(value, str)
            new_entry[self.prefix + field] = value
            changes.append(Changes(field, value, bib_field.source))

        dump.new_fields = len(changes)
        if changes != []:
            self.changed_entries += 1
            self.changed_fields += len(changes)
            self.changes.append((entry_id, changes))
        logger.verbose_info(
            BULLET + "{StBold}{entry}{StBoldOff} {nb} new fields",
            entry=entry_id.ljust(self.get_id_padding()),
            nb=len(changes),
        )
        self.dumps.append(dump)
        if self.mark:
            new_entry[MARKED_FIELD] = datetime.today().strftime("%Y-%m-%d")
        if self.diff_mode:
            if len(new_entry) > (1 if self.mark else 0):
                new_entry["ID"] = entry_id
                new_entry["ENTRYTYPE"] = entry.get("ENTRYTYPE", "unknown")
            else:
                new_entry = dict()
            entry.clear()
        entry.update(new_entry)

    def combine_field(
        self, results: List[BibtexEntry], fieldname: FieldType, entry_name: str
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
            if elt.value is not None and elt.slow_check(elt.value, entry_name):
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
                    "{value}{FgWhite}{StFaint}}},{Reset}\n"
                    "    {FgGreen}{StItalics}% source: {source}{Reset}",
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

    def write_file(self, files: Union[PathType, List[PathType]]) -> None:
        """Writes the databases in self to the given files
        If not enough files, an error is raised.
        If too many files, extras are ignored"""
        if not isinstance(files, list):
            files = [files]
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
            wrote += file_write(file, db, self.writer)
        logger.info(
            "Wrote {total} {files}",
            total=wrote,
            files="file" if wrote == 1 else "files",
        )

    def write_string(self) -> List[str]:
        """Returns the bibtex string representation of the databases"""
        bibs = []
        for db in self.bibdatabases:
            bibs.append(write(db, self.writer))
        return bibs

    def write_entry(self) -> List[List[EntryType]]:
        """Returns the dict representation of the databases"""
        return [bib.entries for bib in self.bibdatabases]

    def load_file(self, files: Union[PathType, List[PathType]]) -> None:
        """Read one or more bibtex files, and adds them to self.bibdatabases
        Creates a separate database for each file"""
        logger.header("Reading files")
        if not isinstance(files, list):
            files = [files]
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
        self.bibdatabases += dbs

    def load_string(self, strings: Union[str, List[str]]) -> None:
        """Read one or more bibtex strings, and adds them to self.bibdatabases
        Creates a separate database for each passed string"""
        if not isinstance(strings, list):
            strings = [strings]
        for string in strings:
            self.bibdatabases.append(read(string))

    def convert_authors(self, entry: EntryType, field: Literal["author", "editor"]) -> EntryType:
        """Convert authors from {'firstname':str|None, 'lastname':str} to a single bibtex string"""
        if field in entry and not isinstance(entry[field], str):
            value = cast(Union[AuthorType, list[AuthorType]], entry[field])
            if not isinstance(value, list):
                value = [value]
            names = []
            for x in value:
                firstname = ""
                if "firstname" in x and x["firstname"]:
                    firstname = str(x["firstname"])
                if "lastname" not in x or not x["lastname"]:
                    raise ValueError(f"Invalid {field} name: expected dict with 'firstname' and 'lastname' attributes")
                lastname = str(x["lastname"])
                if firstname:
                    names.append(f"{lastname}, {firstname}")
                else:
                    names.append(lastname)
        entry[field] = " and ".join(names)
        return entry

    def load_entry(self, entries: Union[EntryType, List[EntryType]]) -> None:
        """Read one or more bibtex entry dicts, and adds them to self.bibdatabases
        Creates a single database for all entries passed
        Entries should be a dict with:
        - keys are lowercase bibtex strings (e.g. entries["title"] = "My Awesome Paper")
        - There are two special keys "ENTRYTYPE" and "ID": ('@article{foo, ...}'
          has "ENTRYTYPE"= "article" and "ID"="foo"
        - values should be string, with the possible exception of author/editor
          which can be specified as a dict with keys 'firstname' and 'lastname'
          or a list of such dicts
        """
        if not isinstance(entries, list):
            entries = [entries]
        db = BibDatabase()
        for entry in entries:
            if "ID" not in entry:
                raise ValueError("Entries should have an 'ID' field")
            entry = self.convert_authors(entry, "author")
            entry = self.convert_authors(entry, "editor")
            db.entries.append(entry)
        self.bibdatabases.append(db)

    def load_stdin(self) -> None:
        """Read a bibtex file from stdin, and adds it to self.bibdatabases
        Waits until end of input before returning"""
        self.load_string("".join(input().readline()))
