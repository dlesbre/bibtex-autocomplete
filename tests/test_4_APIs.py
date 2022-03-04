from logging import DEBUG

from bibtexautocomplete.APIs import (
    CrossrefLookup,
    DBLPLookup,
    ResearchrLookup,
    UnpaywallLookup,
)
from bibtexautocomplete.bibtex.entry import BibtexEntry
from bibtexautocomplete.lookups.abstract_base import LookupType
from bibtexautocomplete.utils.logger import logger

logger.setLevel(DEBUG)

entry1 = {
    "plain_title": "Reactive Path Deformation for Nonholonomic Mobile Robots",
    "title": "Reactive Path Deformation for Nonholonomic Mobile Robots",
    "plain_author": "Lamiraux Bonnafous",
    "author": "Lamiraux Bonnafous",
    "ID": "Lam",
}
doi1 = "10.1109/tro.2004.829459"
entry2 = {
    "plain_title": "Cephalopode: A custom processor aimed at functional language execution for IoT devices",
    "title": "Cephalopode: A custom processor aimed at functional language execution for IoT devices",
    "plain_author": "Carl-Johan H Seger",
    "author": "Carl-Johan H Seger",
    "ID": "Cephalopode",
}
doi2 = "10.1109/memocode51338.2020.9315094"

entry_junk = {
    "plain_title": "156231.0649 404 nonexistant",
    "title": "156231.0649 404 nonexistant",
    "plain_author": "No one",
    "author": "No one",
    "ID": "THIS_IS_NOT_A_PUBLICATION",
}

entry_invalid = {"some junk": "some other junk"}


class Base:
    Lookup: LookupType
    entry = (entry2, doi2)

    def test_valid(self):
        a = self.Lookup(BibtexEntry(self.entry[0]))
        res = a.query()
        assert res is not None
        assert res.doi == self.entry[1]

    def test_junk(self):
        a = self.Lookup(BibtexEntry(entry_junk))
        assert a.query() is None

    def test_invalid(self):
        a = CrossrefLookup(BibtexEntry(entry_invalid))
        assert a.query() is None

    def test_no_author(self):
        entry = self.entry[0].copy()
        del entry["author"]
        del entry["plain_author"]
        a = self.Lookup(BibtexEntry(entry))
        res = a.query()
        assert res is not None
        assert res.doi == self.entry[1]

    def test_no_title(self):
        entry = self.entry[0].copy()
        del entry["title"]
        del entry["plain_title"]
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
