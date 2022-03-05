from bibtexautocomplete.bibtex.author import Author
from bibtexautocomplete.bibtex.entry import (
    BibtexEntry,
    FieldNames,
    FieldNamesSet,
    SpecialFields,
)
from bibtexautocomplete.bibtex.io import file_read, write
from bibtexautocomplete.bibtex.normalize import (
    EN_MONTHS,
    normalize_doi,
    normalize_month,
    normalize_str,
    normalize_str_weak,
)


def test_normalize_str_weak():
    tests = [
        ("abc", "abc"),
        ("a.b.c", "a.b.c"),
        ("a  b\t\n\rc\nd", "a b c d"),
        ("ABC", "abc"),
        ("12 +*-/#.?:$%", "12 +*-/#.?:$%"),
        ("àbcéèçôêâû+ÏÖÜÉÀÈÇÉ#!;§", "abceecoeau+ioueaece#!;§"),
    ]
    for inp, out in tests:
        assert normalize_str_weak(inp) == out


def test_normalize_str():
    tests = [
        ("abc", "abc"),
        ("a.b.c", "a b c"),
        ("a  b\t\n\rc\nd", "a b c d"),
        ("ABC", "abc"),
        ("12 +*-/#.?:$%", "12"),
        ("àbcéèçôêâû+ÏÖÜÉÀÈÇÉ#!;§", "abceecoeau ioueaece"),
    ]
    for inp, out in tests:
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


def test_get_authors():
    for author, res in authors:
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


def test_BibtexEntry_author_get():
    for author, res in authors:
        b = BibtexEntry({FieldNames.AUTHOR: author})
        assert b.author == res


def test_BibtexEntry_editor_get():
    for author, res in authors:
        b = BibtexEntry({FieldNames.EDITOR: author})
        assert b.editor == res


def test_BibtexEntry_author_set():
    for author, res in authors:
        b = BibtexEntry()
        b.author = res
        assert b.author == res


def test_BibtexEntry_editor_set():
    for author, res in authors:
        b = BibtexEntry()
        b.editor = res
        assert b.editor == res
