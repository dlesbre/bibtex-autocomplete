from argparse import ArgumentParser
from pathlib import Path
from sys import stdout
from typing import List, Optional, TypeVar

from .abstractlookup import ABaseLookup
from .autocomplete import BibtexAutocomplete
from .defs import (
    CONNECTION_TIMEOUT,
    NAME,
    PROGRESS,
    VERSION,
    OnlyExclude,
    logger,
    set_logger_level,
)
from .lookup import LOOKUP_NAMES, LOOKUPS

parser = ArgumentParser(prog=NAME, add_help=False)

parser.add_argument(
    "--dont-query", "-Q", nargs=1, action="append", default=[], choices=LOOKUP_NAMES
)
parser.add_argument(
    "--only-query", "-q", nargs=1, action="append", default=[], choices=LOOKUP_NAMES
)
parser.add_argument(
    "--dont-complete",
    "-C",
    nargs=1,
    action="append",
    default=[],
)
parser.add_argument(
    "--only-complete",
    "-c",
    nargs=1,
    action="append",
    default=[],
)
parser.add_argument("--exclude-entry", "-E", nargs=1, action="append", default=[])
parser.add_argument("--only-entry", "-e", nargs=1, action="append", default=[])

parser.add_argument("--force-overwrite", "-f", action="store_true")
parser.add_argument("--inplace", "-i", action="store_true")
parser.add_argument("--timeout", "-t", nargs=1, type=float, default=CONNECTION_TIMEOUT)
parser.add_argument("--verbose", "-v", action="count", default=0)
parser.add_argument("--silent", "-s", action="store_true")
parser.add_argument("--no-color", "-n", action="store_true")

parser.add_argument("--version", action="store_true")
parser.add_argument("--help", "-h", action="store_true")

parser.add_argument("--output", "-o", nargs=1, type=Path, action="append", default=[])
parser.add_argument("input", nargs="*", type=Path, action="append", default=[])

HELP_TEXT = """{b}{NAME}{e} version {VERSION}
Program to autocomplete bibtex entries by searching online databases.
Polls the following databases:
  {LOOKUPS}

Usage:
  {b}{NAME}{e} {c}[--flags] <input_files>{e}

Example:
  {b}{NAME}{e} {c}my_bib.bib{e}         print to stdout
  {b}{NAME}{e} {c}-i my_bib.bib{e}      inplace modify
  {b}{NAME}{e} {c}a.bib -o b.bib c.bib -o d.bib{e}
      writes completed a.bib in b.bib and c.bib in d.bib

Optional arguments: can all be used multiple times
  {c}-o --output{e} {d}<file>{e}          Write output to given file
            With multiple input/outputs they are mapped in appearance order
            Extra inputs are dumped on stdout

  {c}-q --only-query{e} {d}<site>{e}      Only query the given sites
  {c}-Q --dont-query{e} {d}<site>{e}      Don't query the given sites
            Site must be one of: {LOOKUPS}

  {c}-e --only-entry{e}    {d}<id>{e}     Only perform lookup these entries
  {c}-E --exclude-entry{e} {d}<id>{e}     Don't perform lookup these entries
            ID is the identifier in bibtex (e.g. @inproceedings{bopen}<id> ... {bclose})

  {c}-c --only-complete{e} {d}<field>{e}  Only complete the given fields
  {c}-C --dont-complete{e} {d}<field>{e}  Don't complete the given fields
            Field is a bibtex field (e.g. 'author', 'doi',...)

Flags:
  {c}-i --inplace{e}          Modify input files inplace, overrides any specified output files
  {c}-f --force-overwrite{e}  Overwrite aldready present fields with data found online
  {c}-t --timeout{e} {d}<float>{e}  set timeout on request, default: {TIMEOUT} s

  {c}-v --verbose{e}          print the commands called
  {c}-s --silent{e}           don't show progressbar (keeps tex output and error messages)
  {c}-n --no-color{e}         don't color output

  {c}--version{e}             show version number
  {c}-h --help{e}             show this help"""

T = TypeVar("T")


def flatten(list_of_lists: List[List[T]]) -> List[T]:
    """flatten a nested list"""
    return [val for sublist in list_of_lists for val in sublist]


def bibtexautocomplete_main(argv: Optional[List[str]] = None) -> None:
    """The main function of bibtexautocomplete
    Takes an argv like List as argument,
    if none, uses sys.argv
    see HELP_TEXT or bibtexautocomplete_main(["-h]) for details"""
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
                bopen="{",
                bclose="}",
                TIMEOUT=CONNECTION_TIMEOUT,
                VERSION=VERSION,
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
        print(f"{NAME} version {VERSION}")
        exit(0)

    if args.silent:
        args.verbose = -1
    set_logger_level(args.verbose)

    if args.inplace:
        args.output = args.input

    if isinstance(args.timeout, list):
        args.timeout = args.timeout[0]
    ABaseLookup.connection_timeout = args.timeout
    lookups = (
        OnlyExclude[str]
        .from_nonempty(args.only_query, args.dont_query)
        .filter(LOOKUPS, lambda x: x.name)
    )
    fields = OnlyExclude[str].from_nonempty(args.only_complete, args.dont_complete)
    entries = OnlyExclude[str].from_nonempty(args.only_entry, args.exclude_entry)

    databases = BibtexAutocomplete.read(flatten(args.input))
    completer = BibtexAutocomplete(
        databases, lookups, fields, entries, args.force_overwrite
    )
    try:
        completer.autocomplete(args.verbose != 0)
        completer.write(flatten(args.output))
    except KeyboardInterrupt:
        logger.log(PROGRESS, "Interrupted")


if __name__ == "__main__":
    bibtexautocomplete_main()
