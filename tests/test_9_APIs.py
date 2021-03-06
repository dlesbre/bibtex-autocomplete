import pytest

from bibtexautocomplete.APIs import (
    ArxivLookup,
    CrossrefLookup,
    DBLPLookup,
    ResearchrLookup,
    UnpaywallLookup,
)
from bibtexautocomplete.APIs.doi import DOICheck, URLCheck
from bibtexautocomplete.bibtex.entry import BibtexEntry
from bibtexautocomplete.lookups.abstract_base import LookupType
from bibtexautocomplete.utils.logger import logger

logger.set_verbosity(4)

entry1 = {
    "title": "Reactive Path Deformation for Nonholonomic Mobile Robots",
    "author": "Lamiraux Bonnafous",
    "ID": "Lam",
}
doi1 = "10.1109/tro.2004.829459"
entry2 = {
    "title": "Cephalopode: A custom processor aimed at functional language execution for IoT devices",
    "author": "Carl-Johan H Seger",
    "ID": "Cephalopode",
}
doi2 = "10.1109/memocode51338.2020.9315094"

entry_junk = {
    "title": "156231.0649 404 nonexistant",
    "author": "No one",
    "ID": "THIS_IS_NOT_A_PUBLICATION",
}

entry_invalid = {"some junk": "some other junk"}

entry3 = {
    "title": "Quantum Criticality for Extended Nodes on a Bethe Lattice in the Large Connectivity Limit",
    "author": "Murray, James M. and Maestro, Adrian Del and Tesanovic, Zlatko",
    "ID": "something",
}
doi3 = "10.1103/physrevb.85.115117"


class Base:
    Lookup: LookupType
    entry = (entry2, doi2)

    def test_valid(self) -> None:
        a = self.Lookup(BibtexEntry(self.entry[0]))
        res = a.query()
        assert res is not None
        assert res.doi == self.entry[1]

    def test_junk(self) -> None:
        a = self.Lookup(BibtexEntry(entry_junk))
        assert a.query() is None

    def test_invalid(self) -> None:
        a = CrossrefLookup(BibtexEntry(entry_invalid))
        assert a.query() is None

    def test_no_author(self) -> None:
        entry = self.entry[0].copy()
        del entry["author"]
        a = self.Lookup(BibtexEntry(entry))
        res = a.query()
        assert res is not None
        assert res.doi == self.entry[1]

    def test_no_title(self) -> None:
        entry = self.entry[0].copy()
        del entry["title"]
        a = self.Lookup(BibtexEntry(entry))
        assert a.query() is None


class TestCrossref(Base):
    Lookup = CrossrefLookup
    entry = (entry1, doi1)


class TestDBLP(Base):
    Lookup = DBLPLookup


class TestResearchr(Base):
    Lookup = ResearchrLookup


class TestUnpaywall(Base):
    Lookup = UnpaywallLookup


class TestArxiv(Base):
    Lookup = ArxivLookup
    entry = (entry3, doi3)


dois = [
    ("not a valid doi", False),
    ("https://doi.org/10.1109/5.771073", True),
    ("10.1109/5.771073", True),
    ("10.1007/978-1-4684-5287-7", False),
    ("10.1007/3-540-46425-5_21", True),
]


@pytest.mark.parametrize(("doi", "valid"), dois)
def test_doi_check(doi: str, valid: bool) -> None:
    d = DOICheck(doi)
    if d.query() is True:
        assert valid is True
    else:
        assert valid is False


urls = [
    ("http://google.com", True),
    ("https://google.com", True),
    ("https://sfkmlj.jl.fs", False),
    ("NOT AN URL", False),
    ("http//sfdq.com/fp", False),
]


@pytest.mark.parametrize(("url", "valid"), urls)
def test_url_check(url: str, valid: bool) -> None:
    d = URLCheck(url)
    if d.query() is not None:
        assert valid is True
    else:
        assert valid is False
