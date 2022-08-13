"""
Command-line argument parser
"""

from argparse import ArgumentParser
from os import listdir
from pathlib import Path
from typing import Iterable, List, TypeVar

from ..APIs import LOOKUP_NAMES
from ..utils.constants import BTAC_FILENAME, CONNECTION_TIMEOUT, SCRIPT_NAME
from ..utils.logger import logger

T = TypeVar("T")


def flatten(list_of_lists: Iterable[List[T]]) -> List[T]:
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
    return Path(input.parent, BTAC_FILENAME.format(name=name, suffix=suffix))


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


def indent_string(indent: str) -> str:
    """Reads and formats an ident string
    whitespace -> whitespace
    "\\t" -> tab
    number -> number of spaces"""
    if indent.isnumeric():
        return " " * int(indent)
    sane = indent.replace("t", "\t").replace("n", "\n").replace("_", " ")
    if not (sane.isspace() or sane == ""):
        logger.critical(
            (
                "--fi/--indent should be a number or string "
                "with spaces, '_', 't' and 'n' only.\nGot: '{}'"
            ).format(indent)
        )
        exit(5)
    return sane


def filter_bibs(files: List[Path]) -> List[Path]:
    """Filter for files ending in .bib
    Ignores generated ".btac.bib" files unless they are the only ones present"""
    bibs = []
    btac_bibs = []
    for file in files:
        if str(file).endswith(BTAC_FILENAME.format(name="", suffix=".bib")):
            btac_bibs.append(file)
        elif file.suffix == ".bib":
            bibs.append(file)
    if bibs:
        return bibs
    return btac_bibs


def get_bibfiles(input: Path) -> List[Path]:
    """Finds bibfiles contained in a folder if given as inputt"""
    if not input.is_dir():
        return [input]
    try:
        files = [input / x for x in listdir(input) if (input / x).is_file()]
    except IOError as err:
        logger.critical(
            "Failed to read '{filepath}': {FgPurple}{err}{Reset}",
            filepath=str(input),
            err=err,
        )
        exit(1)
    return filter_bibs(files)


parser = ArgumentParser(
    prog=SCRIPT_NAME,
    add_help=False,
    usage="btac [--options] <input_files>\nSee help for a list of options.\n",
)

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
parser.add_argument("--ignore-ssl", "-S", action="store_true")

parser.add_argument("--version", action="store_true")
parser.add_argument("--help", "-h", action="store_true")

parser.add_argument("--dump-data", "-d", type=Path)
parser.add_argument("--no-output", "-O", action="store_true")
parser.add_argument("--output", "-o", type=Path, action="append", default=[])
parser.add_argument("input", nargs="*", type=Path, action="append", default=[])

HELP_TEXT = """{StBold}{FgYellow}{NAME}{Reset} {StBold}version {VERSION}{Reset}
Program to autocomplete bibtex entries by searching online databases.
Polls the following databases:
  {LOOKUPS}

{StBold}Usage:{Reset}
  {StBold}{FgYellow}{NAME}{Reset} {FgYellow}[--flags] <input_files>{Reset}

{StBold}Example:{Reset}
  {StBold}{FgYellow}{NAME}{Reset} {FgYellow}my_bib.bib{Reset}         writes to my_bib.btac.bib
  {StBold}{FgYellow}{NAME}{Reset} {FgYellow}-i my_bib.bib{Reset}      inplace modify
  {StBold}{FgYellow}{NAME}{Reset} {FgYellow}a.bib -o b.bib c.bib -o d.bib{Reset}
      writes completed a.bib in b.bib and c.bib in d.bib

{StBold}Optional arguments:{Reset} can all be used multiple times
  {FgYellow}-o --output{Reset} {FgGreen}<file.bib>{Reset}      Write output to given file
        With multiple input/outputs they are mapped in appearance order
        Extra inputs are dumped on stdout

  {FgYellow}-q --only-query{Reset} {FgGreen}<website>{Reset}   Only query the given sites
  {FgYellow}-Q --dont-query{Reset} {FgGreen}<website>{Reset}   Don't query the given sites
        Website must be one of: {LOOKUPS}

  {FgYellow}-e --only-entry{Reset}    {FgGreen}<id>{Reset}     Only perform lookup these entries
  {FgYellow}-E --exclude-entry{Reset} {FgGreen}<id>{Reset}     Don't perform lookup these entries
        ID is the identifier in bibtex (e.g. @inproceedings{{<id> ... }})

  {FgYellow}-c --only-complete{Reset} {FgGreen}<field>{Reset}  Only complete the given fields
  {FgYellow}-C --dont-complete{Reset} {FgGreen}<field>{Reset}  Don't complete the given fields
        Field is a bibtex field (e.g. 'author', 'doi',...)

{StBold}Output formatting:{Reset}
  {FgYellow}--fa --align-values{Reset}        pad fieldnames to align all values
  {FgYellow}--fc --comma-first{Reset}         comma first syntax (, title = ...)
  {FgYellow}--fl --no-trailing-comma{Reset}   don't add a last trailing comma
  {FgYellow}--fi --indent{Reset} {FgGreen}<space>{Reset}      space used for indentation, default is a tab
        Can be specified as an number (number of space) or a string with spaces
        and '_' 't' 'n' characters to mark space, tabs and newlines.

{StBold}Flags:{Reset}
  {FgYellow}-i --inplace{Reset}          Modify input files inplace
        ignores any specified output files
  {FgYellow}-f --force-overwrite{Reset}  Overwrite already present fields
        The default is to overwrite a field if it is empty or absent
  {FgYellow}-t --timeout{Reset} {FgGreen}<float>{Reset}  set timeout on request, default: {TIMEOUT} s
  {FgYellow}-S --ignore-ssl{Reset}       Ignore SSL verification when performing queries

  {FgYellow}-d --dump-data{Reset} {FgGreen}<file.json>{Reset} writes all data from matching entries to
        the given file in JSON format, so data from multiple sources can be compared
  {FgYellow}-O --no-output{Reset}        Don't write any output files (except the --dump-data file)

  {FgYellow}-v --verbose{Reset}          increase verbosity (use up to 3 times)
  {FgYellow}-s --silent{Reset}           decrease verbosity (use up to 4 times)
  {FgYellow}-n --no-color{Reset}         don't color/stylise output

  {FgYellow}--version{Reset}             show version number
  {FgYellow}-h --help{Reset}             show this help

{StBold}Source and Bug reports:{Reset}
  The source code is available under an {LICENSE} License on github:
  {StUnderline}{URL}{Reset}

  You can report bugs there using the issue tracker."""
