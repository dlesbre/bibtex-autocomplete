from typing import List

import pytest

from bibtexautocomplete.core import main

PREFIX = "./tests/"
EMPTY_BIB = PREFIX + "test_2.bib"

args = [
    ["-h"],
    ["--help"],
    ["--version"],
    [EMPTY_BIB, "-v"],
    [EMPTY_BIB, "-i"],
    [EMPTY_BIB, "--inplace"],
]


@pytest.mark.parametrize("args", args)
def test_with_args(args: List[str]) -> None:
    main(args)
