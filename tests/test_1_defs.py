"""Tests for functions/classes in bibtexautcomplete/defs"""

from bibtexautocomplete import defs


def test_str_normalize():
    tests = [
        ("abc", "abc"),
        ("a.b.c", "a b c"),
        ("a  b\tc\nd", "a b c d"),
        ("ABC", "abc"),
        ("12 +*-/#.", "12"),
    ]
    for inp, out in tests:
        assert defs.str_normalize(inp) == out
