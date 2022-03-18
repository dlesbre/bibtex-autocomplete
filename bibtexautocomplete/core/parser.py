"""
Command-line argument parser
"""

from argparse import ArgumentParser
from pathlib import Path
from typing import TypeVar

from ..APIs import LOOKUP_NAMES
from ..utils.constants import CONNECTION_TIMEOUT, NAME

T = TypeVar("T")


def flatten(list_of_lists: list[list[T]]) -> list[T]:
    """flatten a nested list"""
    return [val for sublist in list_of_lists for val in sublist]


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

HELP_TEXT = """{StBold}{FgYellow}{NAME}{StBoldOff}{FgReset} version {VERSION}
Program to autocomplete bibtex entries by searching online databases.
Polls the following databases:
  {LOOKUPS}

Usage:
  {StBold}{FgYellow}{NAME}{StBoldOff}{FgReset} {FgYellow}[--flags] <input_files>{FgReset}

Example:
  {StBold}{FgYellow}{NAME}{StBoldOff}{FgReset} {FgYellow}my_bib.bib{FgReset}         print to stdout
  {StBold}{FgYellow}{NAME}{StBoldOff}{FgReset} {FgYellow}-i my_bib.bib{FgReset}      inplace modify
  {StBold}{FgYellow}{NAME}{StBoldOff}{FgReset} {FgYellow}a.bib -o b.bib c.bib -o d.bib{FgReset}
      writes completed a.bib in b.bib and c.bib in d.bib

Optional arguments: can all be used multiple times
  {FgYellow}-o --output{FgReset} {FgGreen}<file>{FgReset}          Write output to given file
            With multiple input/outputs they are mapped in appearance order
            Extra inputs are dumped on stdout

  {FgYellow}-q --only-query{FgReset} {FgGreen}<site>{FgReset}      Only query the given sites
  {FgYellow}-Q --dont-query{FgReset} {FgGreen}<site>{FgReset}      Don't query the given sites
            Site must be one of: {LOOKUPS}

  {FgYellow}-e --only-entry{FgReset}    {FgGreen}<id>{FgReset}     Only perform lookup these entries
  {FgYellow}-E --exclude-entry{FgReset} {FgGreen}<id>{FgReset}     Don't perform lookup these entries
            ID is the identifier in bibtex (e.g. @inproceedings{{<id> ... }})

  {FgYellow}-c --only-complete{FgReset} {FgGreen}<field>{FgReset}  Only complete the given fields
  {FgYellow}-C --dont-complete{FgReset} {FgGreen}<field>{FgReset}  Don't complete the given fields
            Field is a bibtex field (e.g. 'author', 'doi',...)

Flags:
  {FgYellow}-i --inplace{FgReset}          Modify input files inplace, overrides any specified output files
  {FgYellow}-f --force-overwrite{FgReset}  Overwrite aldready present fields with data found online
  {FgYellow}-t --timeout{FgReset} {FgGreen}<float>{FgReset}  set timeout on request, default: {TIMEOUT} s

  {FgYellow}-v --verbose{FgReset}          print the commands called
  {FgYellow}-s --silent{FgReset}           don't show progressbar (keeps tex output and error messages)
  {FgYellow}-n --no-color{FgReset}         don't color output

  {FgYellow}--version{FgReset}             show version number
  {FgYellow}-h --help{FgReset}             show this help"""
