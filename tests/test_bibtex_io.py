from bibtexautocomplete import bibtex


def iotest(file: str) -> None:
    db = bibtex.read(file)
    bibtex.write(db)


def test_io_0():
    iotest("tests/test_0.bib")


def test_io_1():
    iotest("tests/test_1.bib")


def test_get_authors():
    authors = [
        ("John Jones", [bibtex.Author("Jones", "John")]),
        (
            "Lewis, C. S. and Douglas Adams",
            [bibtex.Author("Lewis", "C. S."), bibtex.Author("Adams", "Douglas")],
        ),
    ]
    for author, res in authors:
        assert bibtex.get_authors({"author": author}) == res
