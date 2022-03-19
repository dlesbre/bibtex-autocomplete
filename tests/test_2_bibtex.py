import pytest

from bibtexautocomplete.bibtex.author import Author
from bibtexautocomplete.bibtex.entry import (
    BibtexEntry,
    FieldNames,
    FieldNamesSet,
    SpecialFields,
)
from bibtexautocomplete.bibtex.io import file_read, write
from bibtexautocomplete.bibtex.matching import (
    ENTRY_CERTAIN_MATCH,
    ENTRY_NO_MATCH,
    match_score,
)
from bibtexautocomplete.bibtex.normalize import (
    EN_MONTHS,
    normalize_doi,
    normalize_month,
    normalize_str,
    normalize_str_weak,
)

tests = [
    ("abc", "abc"),
    ("a.b.c", "a.b.c"),
    ("a  b\t\n\rc\nd", "a b c d"),
    ("ABC", "abc"),
    ("12 +*-/#.?:$%", "12 +*-/#.?:$%"),
    ("àbcéèçôêâû+ÏÖÜÉÀÈÇÉ#!;§", "abceecoeau+ioueaece#!;§"),
]


@pytest.mark.parametrize(("inp", "out"), tests)
def test_normalize_str_weak(inp, out):
    assert normalize_str_weak(inp) == out


tests = [
    ("abc", "abc"),
    ("a.b.c", "a b c"),
    ("a  b\t\n\rc\nd", "a b c d"),
    ("ABC", "abc"),
    ("12 +*-/#.?:$%", "12"),
    ("àbcéèçôêâû+ÏÖÜÉÀÈÇÉ#!;§", "abceecoeau ioueaece"),
]


@pytest.mark.parametrize(("inp", "out"), tests)
def test_normalize_str(inp, out):
    assert normalize_str(inp) == out


def test_normalize_doi():
    doi = [
        "10.1000/123456",
        "10.1038/issn.1476-4687",
        "10.1111/dome.1208",
        "10.1111/josi.12122",
    ]
    prefixes = ["", "https://www.doi.org/", "https://somedomain.com/some/path/"]
    for d in doi:
        for p in prefixes:
            assert normalize_doi(p + d) == d


def test_normalize_month():
    for month, norm in EN_MONTHS.items():
        assert normalize_month(month) == str(norm)
    for month in ("bla", "not.a.month", "6496489", "#!!0"):
        assert normalize_month(month) == month


def io_test(file: str) -> None:
    db = file_read(file)
    write(db)


def test_case():
    db = file_read("tests/test_0.bib")
    assert "author" in db.entries[0]


def test_io_0():
    io_test("tests/test_0.bib")


def test_io_1():
    io_test("tests/test_1.bib")


authors = [
    ("John Jones", [Author("Jones", "John")]),
    (
        "Lewis, C. S. and Douglas Adams",
        [Author("Lewis", "C. S."), Author("Adams", "Douglas")],
    ),
    ("", []),
]


@pytest.mark.parametrize(("author", "res"), authors)
def test_get_authors(author, res):
    assert Author.from_namelist(author) == res


def test_BibtexEntry_normal():
    a = BibtexEntry()
    for field in FieldNamesSet - SpecialFields:
        assert getattr(a, field) is None
        setattr(a, field, field)
    for field in FieldNamesSet - SpecialFields:
        assert getattr(a, field) == field


def test_BibtexEntry_special():
    a = BibtexEntry({})
    for field in SpecialFields:
        val = getattr(a, field)
        if field in ("author", "editor"):
            assert val == []
            setattr(a, field, [])
        else:
            assert val is None
            setattr(a, field, None)


@pytest.mark.parametrize(("author", "res"), authors)
def test_BibtexEntry_author_get(author, res):
    b = BibtexEntry({FieldNames.AUTHOR: author})
    assert b.author == res


@pytest.mark.parametrize(("author", "res"), authors)
def test_BibtexEntry_editor_get(author, res):

    b = BibtexEntry({FieldNames.EDITOR: author})
    assert b.editor == res


@pytest.mark.parametrize(("author", "res"), authors)
def test_BibtexEntry_author_set(author, res):
    b = BibtexEntry()
    b.author = res
    assert b.author == res


@pytest.mark.parametrize(("author", "res"), authors)
def test_BibtexEntry_editor_set(author, res):
    b = BibtexEntry()
    b.editor = res
    assert b.editor == res


def test_matching():
    assert match_score(BibtexEntry(), BibtexEntry()) == ENTRY_NO_MATCH
    doi1 = BibtexEntry({"doi": "10.1234/12345"})
    doi2 = BibtexEntry({"doi": "10.1234/different.12345"})
    assert match_score(doi1, doi1) == ENTRY_CERTAIN_MATCH
    assert match_score(doi1, doi2) == ENTRY_NO_MATCH
    title1 = BibtexEntry({"title": "My\tawesome paper!"})
    title1_v = BibtexEntry({"title": "My Awesome Paper"})
    title2 = BibtexEntry({"title": "My book, volume 1"})
    title2_v = BibtexEntry({"title": "My book, volume 2"})
    titles = [title1, title1_v, title2, title2_v]
    for title in titles:
        for t in titles:
            assert match_score(title, title) >= match_score(title, t)
            assert match_score(t, title) == match_score(title, t)
        assert match_score(title, title) > ENTRY_NO_MATCH
    assert match_score(title1, title1_v) > ENTRY_NO_MATCH
    assert match_score(title2, title2_v) == ENTRY_NO_MATCH
