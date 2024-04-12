from typing import Dict, List, NamedTuple, Optional

from bibtexautocomplete.bibtex.entry import BibtexEntry
from bibtexautocomplete.bibtex.normalize import normalize_str
from bibtexautocomplete.lookups.abstract_base import AbstractLookup
from bibtexautocomplete.lookups.multiple_mixin import DAT_Query_Mixin


class ToCheck(NamedTuple):
    title: Optional[str]
    doi: Optional[str]
    author: Optional[List[str]]


class SearchEval(AbstractLookup[BibtexEntry, BibtexEntry]):
    index: int = 0
    expected: List[ToCheck] = []

    doi: Optional[str]
    title: Optional[str]
    authors: Optional[List[str]]

    def query(self) -> Optional[BibtexEntry]:
        test = self.expected[self.index]
        assert self.doi == test.doi
        assert self.authors == test.author
        title = None if test.title is None else normalize_str(test.title)
        assert self.title == title
        self.index += 1
        return None


class TestDATQuery:
    class parent(DAT_Query_Mixin, SearchEval):
        def __repr__(self) -> str:
            return f"<doi:{self.doi}; author:{self.authors}; title:{self.title}>"

    def make_query(self, expected: List[ToCheck], entry: Dict[str, str]) -> None:
        bib = BibtexEntry.from_entry("test", entry)
        p = self.parent(bib)
        p.index = 0
        p.expected = expected
        assert p.query() is None
        assert p.index == len(p.expected)

    def test_empty(self) -> None:
        self.make_query([], {})

    def test_all(self) -> None:
        title = "This is a title++"
        authors = ["Alp", "Rom", "Bob"]
        doi = "10.1234/123456"
        entry = {"doi": doi, "author": " and ".join(authors), "title": title}
        expected: List[ToCheck] = [
            ToCheck(doi=doi, author=authors, title=title),
            ToCheck(doi=None, author=authors, title=title),
            ToCheck(doi=None, author=None, title=title),
        ]
        self.make_query(expected, entry)

    def test_no_doi(self) -> None:
        title = "this is a title"
        authors = ["Alp", "Rom", "Bob"]
        entry = {
            "author": " and ".join(authors),
            "title": title,
        }
        expected: List[ToCheck] = [
            ToCheck(doi=None, author=authors, title=title),
            ToCheck(doi=None, author=None, title=title),
        ]
        self.make_query(expected, entry)

    def test_no_author(self) -> None:
        title = "this Is A title"
        doi = "10.1234/123456"
        entry = {
            "doi": doi,
            "title": title,
        }
        expected: List[ToCheck] = [
            ToCheck(doi=doi, author=None, title=title),
            ToCheck(doi=None, author=None, title=title),
        ]
        self.make_query(expected, entry)

    def test_no_title(self) -> None:
        authors = ["Alp", "Rom", "Bob"]
        doi = "10.1234/123456"
        entry = {
            "doi": doi,
            "author": " and ".join(authors),
        }
        expected: List[ToCheck] = [
            ToCheck(doi=doi, author=authors, title=None),
        ]
        self.make_query(expected, entry)

    def test_no_doi_author(self) -> None:
        title = "This is a title"
        entry = {"title": title}
        expected: List[ToCheck] = [
            ToCheck(doi=None, author=None, title=title),
        ]
        self.make_query(expected, entry)


class TestDTQuery:
    class parent(DAT_Query_Mixin, SearchEval):
        query_author_title: bool = False

        def __repr__(self) -> str:
            return f"<doi:{self.doi}; title:{self.title}>"

    def make_query(self, expected: List[ToCheck], entry: Dict[str, str]) -> None:
        bib = BibtexEntry.from_entry("test", entry)
        p = self.parent(bib)
        p.index = 0
        p.expected = expected
        assert p.query() is None
        assert p.index == len(p.expected)

    def test_empty(self) -> None:
        self.make_query([], {})

    def test_all(self) -> None:
        title = "This is a title"
        doi = "10.1234/123456"
        entry = {"doi": doi, "title": title}
        expected: List[ToCheck] = [
            ToCheck(doi=doi, author=None, title=title),
            ToCheck(doi=None, author=None, title=title),
        ]
        self.make_query(expected, entry)

    def test_no_doi(self) -> None:
        title = "This is a title"
        entry = {
            "title": title,
        }
        expected: List[ToCheck] = [ToCheck(doi=None, author=None, title=title)]
        self.make_query(expected, entry)

    def test_no_title(self) -> None:
        doi = "10.1234/123456"
        entry = {
            "doi": doi,
        }
        expected: List[ToCheck] = [
            ToCheck(doi=doi, author=None, title=None),
        ]
        self.make_query(expected, entry)


class ConditionEval(AbstractLookup[BibtexEntry, BibtexEntry]):
    queried: bool

    def __init__(self, entry: BibtexEntry) -> None:
        self.queried = False
        super().__init__(entry)

    def query(self) -> Optional[BibtexEntry]:
        self.queried = True
        return None
