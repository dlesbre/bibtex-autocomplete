"""Tests for functions/classes in bibtexautcomplete/defs"""

from typing import List

import pytest

from bibtexautocomplete.utils.only_exclude import OnlyExclude
from bibtexautocomplete.utils.safe_json import SafeJSON

tests = [
    [[1, 2, 3], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]],
    [[], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]],
    [[1, 2, 3, 4, 5, 6, 7, 8, 9], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]],
    [[1, 2, 3], []],
]


@pytest.mark.parametrize(("test", "glob"), tests)
def test_OnlyExclude_only(test: List[int], glob: List[int]) -> None:
    a = OnlyExclude(test, None)
    b = OnlyExclude[int].from_nonempty(test, [])
    for i in glob + test:
        if i in test:
            assert i in a
            assert i in b
        else:
            assert i not in a
            if test == []:
                assert i in b
            else:
                assert i not in b
    res = []
    for x in glob:
        if x in test:
            res.append(x)
    assert list(a.filter(glob, lambda x: x)) == res


@pytest.mark.parametrize(("test", "glob"), tests)
def test_OnlyExclude_exclude(test: List[int], glob: List[int]) -> None:
    a = OnlyExclude(None, test)
    b = OnlyExclude[int].from_nonempty([], test)
    for i in glob + test:
        if i in test:
            assert i not in a
            assert i not in b
        else:
            assert i in a
            assert i in b
    res = []
    for x in glob:
        if x not in test:
            res.append(x)
    # Only valid if glob contains test
    assert list(a.filter(glob, lambda x: x)) == res


def test_SafeJSON() -> None:
    a = SafeJSON({"a": 5, "b": "bonjour", "c": [1, 2, {"3": 5, "4": [True, False]}]})
    assert a[0].value is None
    assert a["a"].to_int() == 5
    assert a["b"].to_str() == "bonjour"
    assert a["c"][0].to_int() == 1
    for key, val in a["c"][3].iter_dict():
        if key == "3":
            assert val.to_int() == 5
        elif key == "4":
            for i, x in enumerate(val.iter_list()):
                assert (i == 0) == x.to_bool()
