from pathlib import Path

import pytest

from bibtexautocomplete.core.parser import indent_string, make_output_name

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


test = [
    ("5", "     "),
    ("0", ""),
    ("", ""),
    ("  ", "  "),
    ("\t\t\t", "\t\t\t"),
    ("tnt_", "\t\n\t "),
    ("  \ttn_ ", "  \t\t\n  "),
]


@pytest.mark.parametrize(("input", "res"), test)
def test_indent(input: str, res: str) -> None:
    assert indent_string(input) == res
