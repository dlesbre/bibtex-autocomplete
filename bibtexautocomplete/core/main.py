from sys import stdout
from typing import Optional

from ..APIs import LOOKUP_NAMES, LOOKUPS
from ..lookups.condition_mixin import FieldConditionMixin
from ..lookups.https import HTTPSLookup
from ..utils.constants import CONNECTION_TIMEOUT, NAME, VERSION_STR
from ..utils.logger import logger
from ..utils.only_exclude import OnlyExclude
from .autocomplete import BibtexAutocomplete
from .parser import HELP_TEXT, flatten, parser


def main(argv: Optional[list[str]] = None) -> None:
    """The main function of bibtexautocomplete
    Takes an argv like List as argument,
    if none, uses sys.argv
    see HELP_TEXT or main(["-h]) for details"""
    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    if stdout.isatty() and not args.no_color:
        # use_color = True
        COLOR_YELLOW = "\033[33;1m"  # "\033[34;1m"
        COLOR_ORANGE = "\033[33m"
        COLOR_GREEN = "\033[32m"
        COLOR_END = "\033[0m"
    else:
        COLOR_YELLOW = ""
        COLOR_ORANGE = ""
        COLOR_GREEN = ""
        COLOR_END = ""

    if args.help:
        print(
            HELP_TEXT.format(
                TIMEOUT=CONNECTION_TIMEOUT,
                VERSION=VERSION_STR,
                LOOKUPS=LOOKUP_NAMES,
                NAME=NAME,
                b=COLOR_YELLOW,
                c=COLOR_ORANGE,
                d=COLOR_GREEN,
                e=COLOR_END,
            )
        )
        exit(0)
    if args.version:
        print(f"{NAME} version {VERSION_STR}")
        exit(0)

    if args.silent:
        args.verbose = -args.silent
    logger.set_verbosity(args.verbose)

    if args.inplace:
        args.output = args.input

    if isinstance(args.timeout, list):
        args.timeout = args.timeout[0]
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

    databases = BibtexAutocomplete.read(flatten(args.input))
    completer = BibtexAutocomplete(
        databases, lookups, fields, entries, args.force_overwrite
    )
    try:
        completer.autocomplete(args.verbose != 0)
        completer.write(flatten(args.output))
    except KeyboardInterrupt:
        logger.info("Interrupted")
