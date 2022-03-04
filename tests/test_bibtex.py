from bibtexautocomplete import bibtex


def io_test(file: str) -> None:
    db = bibtex.read(file)
    bibtex.write(db)


def test_case():
    db = bibtex.read("tests/test_0.bib")
    assert "author" in db.entries[0]


def test_io_0():
    io_test("tests/test_0.bib")


def test_io_1():
    io_test("tests/test_1.bib")


authors = [
    ("John Jones", [bibtex.Author("Jones", "John")]),
    (
        "Lewis, C. S. and Douglas Adams",
        [bibtex.Author("Lewis", "C. S."), bibtex.Author("Adams", "Douglas")],
    ),
    ("", []),
]


def test_get_authors():
    for author, res in authors:
        assert bibtex.Author.from_namelist(author) == res


def test_BibtexEntry_normal():
    a = bibtex.BibtexEntry()
    for field in bibtex.FieldNamesSet - bibtex.SpecialFields:
        assert getattr(a, field) is None
        setattr(a, field, field)
    for field in bibtex.FieldNamesSet - bibtex.SpecialFields:
        assert getattr(a, field) == field


def test_BibtexEntry_special():
    a = bibtex.BibtexEntry({})
    for field in bibtex.SpecialFields:
        val = getattr(a, field)
        if field in ("author", "editor"):
            assert val == []
            setattr(a, field, [])
        else:
            assert val is None
            setattr(a, field, None)


def test_BibtexEntry_author_get():
    for author, res in authors:
        b = bibtex.BibtexEntry({bibtex.FieldNames.AUTHOR: author})
        assert b.author == res


def test_BibtexEntry_editor_get():
    for author, res in authors:
        b = bibtex.BibtexEntry({bibtex.FieldNames.EDITOR: author})
        assert b.editor == res


def test_BibtexEntry_author_set():
    for author, res in authors:
        b = bibtex.BibtexEntry({})
        b.author = res
        assert b.author == res


def test_BibtexEntry_editor_set():
    for author, res in authors:
        b = bibtex.BibtexEntry({})
        b.editor = res
        assert b.editor == res
