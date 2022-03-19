"""
Command-line argument parser
"""

from argparse import ArgumentParser
from pathlib import Path
from typing import List, TypeVar

from ..APIs import LOOKUP_NAMES
from ..utils.constants import BTAC_FILENAME, CONNECTION_TIMEOUT, SCRIPT_NAME
from ..utils.logger import logger

T = TypeVar("T")


def flatten(list_of_lists: List[List[T]]) -> List[T]:
    """flatten a nested list"""
    return [val for sublist in list_of_lists for val in sublist]


def make_output_name(input: Path) -> Path:
    """Returns the new renamed path
    e.g. example.bib -> example.btac.bib"""
    name = input.name
    suffix = ""
    if "." in name:
        split = name.split(".")
        suffix = "." + split.pop()
        name = ".".join(split)
    return Path(input.root, BTAC_FILENAME.format(name=name, suffix=suffix))


def make_output_names(inputs: List[Path], outputs: List[Path]) -> List[Path]:
    """Returns output names
    - the first ones are taken from outputs
    - if outputs < inputs, uses inputs with renaming xxx.bib -> xxx.btac.bib
    - if inputs < outputs, issues a warning"""
    len_inputs = len(inputs)
    len_outputs = len(outputs)
    if len_outputs > len_inputs:
        logger.warn(
            "Too many output files specified: got {outs} for {ins} input files",
            outs=len_outputs,
            ins=len_inputs,
        )
    for ii in range(len_outputs, len_inputs, 1):
        outputs.append(make_output_name(inputs[ii]))
    return outputs


parser = ArgumentParser(prog=SCRIPT_NAME, add_help=False)

parser.add_argument(
    "--dont-query", "-Q", action="append", default=[], choices=LOOKUP_NAMES
)
parser.add_argument(
    "--only-query", "-q", action="append", default=[], choices=LOOKUP_NAMES
)
parser.add_argument(
    "--dont-complete",
    "-C",
    action="append",
    default=[],
)
parser.add_argument(
    "--only-complete",
    "-c",
    action="append",
    default=[],
)
parser.add_argument("--exclude-entry", "-E", action="append", default=[])
parser.add_argument("--only-entry", "-e", action="append", default=[])

parser.add_argument("--align-values", "--fa", action="store_true")
parser.add_argument("--comma-first", "--fc", action="store_true")
parser.add_argument("--no-trailing-comma", "--fl", action="store_false")
parser.add_argument("--indent", "--fi", default="\t")

parser.add_argument("--force-overwrite", "-f", action="store_true")
parser.add_argument("--inplace", "-i", action="store_true")
parser.add_argument("--timeout", "-t", type=float, default=CONNECTION_TIMEOUT)
parser.add_argument("--verbose", "-v", action="count", default=0)
parser.add_argument("--silent", "-s", action="store_true")
parser.add_argument("--no-color", "-n", action="store_true")

parser.add_argument("--version", action="store_true")
parser.add_argument("--help", "-h", action="store_true")

parser.add_argument("--output", "-o", type=Path, action="append", default=[])
parser.add_argument("input", nargs="*", type=Path, action="append", default=[])

HELP_TEXT = """{StBold}{FgYellow}{NAME}{StBoldOff}{FgReset} version {VERSION}
Program to autocomplete bibtex entries by searching online databases.
Polls the following databases:
  {LOOKUPS}

Usage:
  {StBold}{FgYellow}{NAME}{StBoldOff}{FgReset} {FgYellow}[--flags] <input_files>{FgReset}

Example:
  {StBold}{FgYellow}{NAME}{StBoldOff}{FgReset} {FgYellow}my_bib.bib{FgReset}         writes to my_bib.btac.bib
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

Output formatting:
  {FgYellow}--fa --align-values{FgReset}        pad fieldnames to align all values)
  {FgYellow}--fc --comma-first{FgReset}         comma first syntax (, title = ...)
  {FgYellow}--fl --no-trailing-comma{FgReset}   don't add a last trailing comma
  {FgYellow}--fi --indent{FgReset} {FgGreen}<space>{FgReset}      space used for indentation, default is a tab

Flags:
  {FgYellow}-i --inplace{FgReset}          Modify input files inplace
        ignores any specified output files
  {FgYellow}-f --force-overwrite{FgReset}  Overwrite aldready present fields
        The default is to overwrite a field if it is empty or absent
  {FgYellow}-t --timeout{FgReset} {FgGreen}<float>{FgReset}  set timeout on request, default: {TIMEOUT} s

  {FgYellow}-v --verbose{FgReset}          increase verbosity (use up to 3 times)
  {FgYellow}-s --silent{FgReset}           decrease verbosity (use up to 4 times)
  {FgYellow}-n --no-color{FgReset}         don't color/stylise output

  {FgYellow}--version{FgReset}             show version number
  {FgYellow}-h --help{FgReset}             show this help"""
