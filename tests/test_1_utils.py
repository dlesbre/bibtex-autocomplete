"""Tests for functions/classes in bibtexautcomplete/defs"""

from typing import List, Optional, Set, Tuple

import pytest

from bibtexautocomplete.utils.functions import (
    list_sort_using,
    list_unduplicate,
    split_iso_date,
)
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


test_undup = [
    ([], ([], set())),
    ([1, 7, 6], ([1, 7, 6], set())),
    ([1, 5, 6, 5, 7], ([1, 5, 6, 7], {5})),
]


@pytest.mark.parametrize(("test", "result"), test_undup)
def test_list_unduplicate(test: List[int], result: Tuple[List[int], Set[int]]) -> None:
    assert list_unduplicate(test) == result


test_sort = [([1, 5, 9, 7], [9, 7, 5, 1]), ([], [])]


@pytest.mark.parametrize(("test", "result"), test_sort)
def test_sort_using(test: List[int], result: List[int]) -> None:
    reference = [9, 8, 7, 6, 5, 4, 3, 2, 1]
    assert list_sort_using(test, reference, lambda x: x) == result


test_split = [
    ("junk", (None, None)),
    ("2020", ("2020", None)),
    ("2020-01", ("2020", "01")),
    ("2020-01-15", ("2020", "01")),
    ("0057-01-15", (None, None)),
    ("2020-33", ("2020", None)),
]


@pytest.mark.parametrize(("test", "result"), test_split)
def test_split_iso_date(test: str, result: Tuple[Optional[str], Optional[str]]) -> None:
    assert split_iso_date(test) == result
