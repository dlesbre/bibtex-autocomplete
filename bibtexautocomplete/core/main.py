from sys import stdout
from typing import List, Optional

from ..APIs import LOOKUP_NAMES, LOOKUPS
from ..bibtex.io import writer
from ..lookups.condition_mixin import FieldConditionMixin
from ..lookups.https import HTTPSLookup
from ..utils.ansi import ANSICodes, ansi_format
from ..utils.constants import CONNECTION_TIMEOUT, LICENSE, SCRIPT_NAME, URL, VERSION_STR
from ..utils.logger import logger
from ..utils.only_exclude import OnlyExclude
from .autocomplete import BibtexAutocomplete
from .parser import HELP_TEXT, flatten, make_output_names, parser


def main(argv: Optional[List[str]] = None) -> None:
    """The main function of bibtexautocomplete
    Takes an argv like List as argument,
    if none, uses sys.argv
    see HELP_TEXT or main(["-h"]) for details"""
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
                LOOKUPS=LOOKUP_NAMES,
                NAME=SCRIPT_NAME,
                URL=URL,
                LICENSE=LICENSE,
            )
        )
        return
    if args.version:
        print("{NAME} version {VERSION}".format(NAME=SCRIPT_NAME, VERSION=VERSION_STR))
        return

    if args.silent:
        args.verbose = -args.silent
    logger.set_verbosity(args.verbose)

    args.input = flatten(args.input)
    if args.inplace:
        if args.output != []:
            logger.warn("Inplace mode, ignoring specified output files")
        args.output = args.input
    else:
        args.output = make_output_names(args.input, args.output)

    writer.align_values = args.align_values
    writer.comma_first = args.comma_first
    writer.add_trailing_comma = args.no_trailing_comma
    writer.indent = args.indent

    HTTPSLookup.connection_timeout = args.timeout
    HTTPSLookup.ignore_ssl = args.ignore_ssl
    lookups = (
        OnlyExclude[str]
        .from_nonempty(args.only_query, args.dont_query)
        .filter(LOOKUPS, lambda x: x.name)
    )
    fields = OnlyExclude[str].from_nonempty(args.only_complete, args.dont_complete)
    entries = OnlyExclude[str].from_nonempty(args.only_entry, args.exclude_entry)

    FieldConditionMixin.fields_to_complete = set(
        fields.filter(FieldConditionMixin.fields_to_complete, lambda x: x)
    )

    databases = BibtexAutocomplete.read(args.input)
    completer = BibtexAutocomplete(
        databases, lookups, fields, entries, args.force_overwrite
    )
    try:
        completer.autocomplete(args.verbose < 0)
        completer.print_changes()
        if args.dump_data is not None:
            completer.write_dumps(args.dump_data)
        if not args.no_output:
            completer.write(args.output)
    except KeyboardInterrupt:
        logger.warn("Interrupted")
