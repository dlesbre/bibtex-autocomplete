from sys import stdout
from typing import List, Optional

from ..APIs import LOOKUP_NAMES, LOOKUPS
from ..lookups.condition_mixin import FieldConditionMixin
from ..lookups.https import HTTPSLookup
from ..utils.ansi import ANSICodes, ansi_format
from ..utils.constants import CONNECTION_TIMEOUT, SCRIPT_NAME, VERSION_STR
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
            )
        )
        exit(0)
    if args.version:
        print("{NAME} version {VERSION}".format(NAME=SCRIPT_NAME, VERSION=VERSION_STR))
        exit(0)

    if args.silent:
        args.verbose = -args.silent
    logger.set_verbosity(args.verbose)

    if args.inplace:
        args.output = args.input
    args.input = flatten(args.input)
    args.output = make_output_names(args.input, args.output)

    HTTPSLookup.connection_timeout = args.timeout
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
        completer.write(args.output)
    except KeyboardInterrupt:
        logger.warn("Interrupted")
