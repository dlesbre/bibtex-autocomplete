from argparse import ArgumentParser
from sys import stdout
from typing import List, Optional

from .abstractlookup import ALookup
from .defs import CONNECTION_TIMEOUT, NAME, VERSION, OnlyExclude
from .lookup import LOOKUP_NAMES, LOOKUPS

parser = ArgumentParser(prog=NAME, add_help=False)

parser.add_argument(
    "--dont-query", "-Q", nargs="?", action="append", default=[], choices=LOOKUP_NAMES
)
parser.add_argument(
    "--only-query", "-q", nargs="?", action="append", default=[], choices=LOOKUP_NAMES
)
parser.add_argument(
    "--dont-complete",
    "-C",
    nargs="?",
    action="append",
    default=[],
)
parser.add_argument(
    "--only-complete",
    "-c",
    nargs="?",
    action="append",
    default=[],
)
parser.add_argument("--exclude-entry", "-E", nargs="?", action="append", default=[])
parser.add_argument("--only-entry", "-e", nargs="?", action="append", default=[])

parser.add_argument("--force-overwrite", "-f", action="store_true")
parser.add_argument("--inplace", "-i", action="store_true")
parser.add_argument("--timeout", "-t", nargs=1, type=float, default=CONNECTION_TIMEOUT)
parser.add_argument("--verbose", "-v", action="store_true")
parser.add_argument("--silent", "-s", action="store_true")
parser.add_argument("--no-color", "-n", action="store_true")

parser.add_argument("--version", action="store_true")
parser.add_argument("--help", "-h", action="store_true")

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


def bibtexautocomplete_main(argv: Optional[List[str]] = None) -> None:
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

    ALookup.connection_timeout = args.timeout
    lookups = (
        OnlyExclude[str]
        .from_nonempty(args.only_query, args.dont_query)
        .to_iterator(LOOKUPS, lambda x: x.name)
    )
    fields = OnlyExclude[str].from_nonempty(args.only_complete, args.dont_complete)
    entries = OnlyExclude[str].from_nonempty(args.only_entry, args.exclude_entry)


if __name__ == "__main__":
    bibtexautocomplete_main()
