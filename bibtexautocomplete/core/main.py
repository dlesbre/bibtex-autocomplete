from pathlib import Path
from sys import stdout
from typing import Container, List, NoReturn, Optional

from ..bibtex.constants import FieldNamesSet, SearchedFields
from ..bibtex.io import make_writer
from ..lookups.https import HTTPSLookup
from ..utils.ansi import ANSICodes, ansi_format
from ..utils.constants import (
    CONNECTION_TIMEOUT,
    FIELD_PREFIX,
    LICENSE,
    MARKED_FIELD,
    SCRIPT_NAME,
    URL,
    VERSION_DATE,
    VERSION_STR,
)
from ..utils.functions import list_sort_using, list_unduplicate
from ..utils.logger import logger
from ..utils.only_exclude import OnlyExclude
from .apis import LOOKUP_NAMES, LOOKUPS
from .autocomplete import BibtexAutocomplete
from .parser import (
    HELP_TEXT,
    MyParser,
    flatten,
    get_bibfiles,
    indent_string,
    make_output_names,
    make_parser,
)


def conflict(parser: MyParser, prefix: str, option1: str, option2: str) -> NoReturn:
    parser.error(
        "{StBold}Conflicting options:\n{Reset}"
        + "  Specified both "
        + prefix
        + "{FgYellow}"
        + option1
        + "{Reset} and a {FgYellow}"
        + option2
        + "{Reset} option."
    )


def main(argv: Optional[List[str]] = None) -> None:
    """The main function of bibtexautocomplete
    Takes an argv like List as argument,
    if none, uses sys.argv
    see HELP_TEXT or main(["-h"]) for details"""
    parser = make_parser()
    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    ANSICodes.use_ansi = stdout.isatty() and not args.no_color

    if args.help:
        print(
            ansi_format(
                HELP_TEXT,
                TIMEOUT=CONNECTION_TIMEOUT,
                VERSION=VERSION_STR,
                VERSION_DATE=VERSION_DATE,
                LOOKUPS=", ".join(LOOKUP_NAMES),
                NAME=SCRIPT_NAME,
                URL=URL,
                LICENSE=LICENSE,
                MARKEDFIELD=MARKED_FIELD,
                PREFIX=FIELD_PREFIX,
            )
        )
        return
    if args.version:
        print(
            "{NAME} version {VERSION} ({VERSION_DATE})".format(
                NAME=SCRIPT_NAME, VERSION=VERSION_STR, VERSION_DATE=VERSION_DATE
            )
        )
        return

    if args.silent:
        args.verbose = -args.silent
    logger.set_verbosity(args.verbose)

    args.input = flatten(args.input)
    # No input -> CWD
    if args.input == []:
        args.input = [Path(".")]
    args.input = flatten(map(get_bibfiles, args.input))
    if args.inplace:
        if args.output != []:
            logger.warn("Inplace mode, ignoring specified output files")
        args.output = args.input
    else:
        args.output = make_output_names(args.input, args.output)

    writer = make_writer()
    writer.align_values = args.align_values
    writer.comma_first = args.comma_first
    writer.add_trailing_comma = args.no_trailing_comma
    writer.indent = indent_string(args.indent)

    HTTPSLookup.connection_timeout = args.timeout if args.timeout > 0.0 else None
    HTTPSLookup.ignore_ssl = args.ignore_ssl
    lookups = OnlyExclude[str].from_nonempty(args.only_query, args.dont_query).filter(LOOKUPS, lambda x: x.name)
    if args.only_query != [] and args.dont_query != []:
        conflict(parser, "a ", "-q/--only-query", "-Q/--dont-query")
    if args.only_query != []:
        # remove duplicate from list
        args.only_query, dups = list_unduplicate(args.only_query)
        if dups:
            # Print set without leading and ending brace
            logger.warn("Duplicate '-q' arguments ignored: {set}", set=str(dups)[1:-1])
        lookups = list_sort_using(lookups, args.only_query, lambda x: x.name)

    fields = OnlyExclude[str].from_nonempty(args.only_complete, args.dont_complete)
    if args.only_complete != [] and args.dont_complete != []:
        conflict(parser, "a ", "-c/--only-complete", "-C/--dont-complete")

    entries = OnlyExclude[str].from_nonempty(args.only_entry, args.exclude_entry)
    if args.only_entry != [] and args.exclude_entry != []:
        conflict(parser, "a ", "-e/--only-entry", "-E/--exclude-entry")

    if args.protect_all_uppercase:
        fields_to_protect_uppercase: Container[str] = FieldNamesSet
    else:
        fields_to_protect_proto = OnlyExclude[str].from_nonempty(args.protect_uppercase, args.dont_protect_uppercase)
        fields_to_protect_proto.default = False
        fields_to_protect_uppercase = fields_to_protect_proto
    if args.protect_all_uppercase != [] and args.protect_uppercase != []:
        conflict(parser, "", "--fpa/--protect-all-uppercase", "--fp/--protect-uppercase")
    if args.protect_all_uppercase != [] and args.dont_protect_uppercase != []:
        conflict(parser, "", "--fpa/--protect-all-uppercase", "--FP/--dont-protect-uppercase")
    if args.protect_uppercase != [] and args.dont_protect_uppercase != []:
        conflict(parser, "a ", "--fp/--protect-uppercase", "--FP/--dont-protect-uppercase")

    overwrite = OnlyExclude[str].from_nonempty(args.overwrite, args.dont_overwrite)
    overwrite.default = False

    if args.diff and args.inplace:
        parser.error(
            "Cannot use {FgYellow}-D/--diff{Reset} flag and {FgYellow}-i/--inplace{Reset} flag "
            "simultaneously, as there\n"
            "       is a big risk of deleting data.\n"
            "       If that is truly what you want to do, specify the output file explictly\n"
            "       with {FgYellow}-o / --output {FgGreen}<filename>{Reset}."
        )

    databases = BibtexAutocomplete.read(args.input)
    completer = BibtexAutocomplete(
        databases,
        lookups,
        set(fields.filter(SearchedFields, lambda x: x)),
        entries,
        force_overwrite=overwrite,
        force_overwrite_all=args.force_overwrite,
        mark=args.mark,
        ignore_mark=args.ignore_mark,
        prefix=args.prefix,
        fields_to_protect_uppercase=fields_to_protect_uppercase,
        escape_unicode=args.escape_unicode,
        diff_mode=args.diff,
        filter_by_entrytype=args.filter_fields_by_entrytype,
    )
    completer.print_filters()
    try:
        completer.autocomplete(args.verbose < 0)
        completer.print_changes()
        if args.dump_data is not None:
            completer.write_dumps(args.dump_data)
        if not args.no_output:
            completer.write(args.output, writer)
    except KeyboardInterrupt:
        logger.warn("Interrupted")
