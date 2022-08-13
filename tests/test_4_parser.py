from pathlib import Path
from typing import List

import pytest

from bibtexautocomplete.core.parser import filter_bibs, indent_string, make_output_name

test = [
    ("ex.bib", "ex.btac.bib"),
    (".bib", ".btac.bib"),
    ("ex", "ex.btac"),
    ("", ".btac"),
    (".", ".btac"),
    ("ex.", "ex.btac."),
    ("folder/ex.bib", "folder/ex.btac.bib"),
    ("f/.bib", "f/.btac.bib"),
    ("f/ex", "f/ex.btac"),
]


@pytest.mark.parametrize(("input", "expected"), test)
def test_make_output_name(input: str, expected: str) -> None:
    assert str(make_output_name(Path(input))) == str(Path(expected))


test1 = [
    ("5", "     "),
    ("0", ""),
    ("", ""),
    ("  ", "  "),
    ("\t\t\t", "\t\t\t"),
    ("tnt_", "\t\n\t "),
    ("  \ttn_ ", "  \t\t\n  "),
]


@pytest.mark.parametrize(("input", "res"), test1)
def test_indent(input: str, res: str) -> None:
    assert indent_string(input) == res


test2 = [
    (["pif", "paf", "pouf"], []),
    (["a.bib", "b.bib", ".bib"], ["a.bib", "b.bib"]),
    (["a.bib", "a.btac.bib", "pif"], ["a.bib"]),
    (["a.btac.bib", "pif"], ["a.btac.bib"]),
]


@pytest.mark.parametrize(("input", "res"), test2)
def test_filter(input: List[str], res: List[str]) -> None:
    path_in = [Path(x) for x in input]
    path_out = [Path(x) for x in res]
    assert filter_bibs(path_in) == path_out
