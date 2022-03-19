from pathlib import Path

import pytest

from bibtexautocomplete.core.parser import make_output_name

test = [
    ("ex.bib", "ex.btac.bib"),
    (".bib", ".btac.bib"),
    ("ex", "ex.btac"),
    ("", ".btac"),
    ("ex.", "ex.btac."),
]


@pytest.mark.parametrize(("input", "expected"), test)
def test_make_output_name(input, expected):
    assert str(make_output_name(Path(input))) == str(Path(expected))
