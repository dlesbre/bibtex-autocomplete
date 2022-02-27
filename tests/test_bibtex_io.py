from bibtexautocomplete.bibtex import read, write


def iotest(file: str) -> None:
    db = read(file)
    write(db)


def test_io_0():
    iotest("tests/test_0.bib")


def test_io_1():
    iotest("tests/test_1.bib")
