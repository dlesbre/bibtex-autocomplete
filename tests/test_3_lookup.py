from typing import Optional

from bibtexautocomplete.bibtex.entry import BibtexEntry
from bibtexautocomplete.lookups.abstract_base import AbstractLookup
from bibtexautocomplete.lookups.multiple_mixin import DATQueryMixin, DTQueryMixin


class SearchEval(AbstractLookup):

    index: int = 0
    expected: list[dict[str, Optional[str]]] = []

    def query(self):
        test = self.expected[self.index]
        if "doi" in test:
            assert getattr(self, "doi") == test["doi"]
        if "author" in test:
            assert getattr(self, "author") == test["author"]
        if "title" in test:
            assert getattr(self, "title") == test["title"]
        self.index += 1
        return None


class TestDATQuery:
    class parent(DATQueryMixin, SearchEval):
        def __repr__(self):
            return f"<doi:{self.doi}; author:{self.author}; title:{self.title}>"

    def make_query(self, expected, entry):
        p = self.parent(BibtexEntry(entry))
        p.index = 0
        p.expected = expected
        assert p.query() is None
        assert p.index == len(p.expected)

    def test_empty(self):
        self.make_query([], {})

    def test_all(self):
        title = "This is a title"
        authors = ["Alp", "Rom", "Bob"]
        doi = "10.1234/123456"
        entry = {"doi": doi, "author": " and ".join(authors), "title": title}
        expected = [
            {"doi": doi, "author": " ".join(authors), "title": title},
            {"doi": None, "author": " ".join(authors), "title": title},
            {"doi": None, "author": authors[0], "title": title},
            {"doi": None, "author": authors[1], "title": title},
            {"doi": None, "author": authors[2], "title": title},
            {"doi": None, "author": None, "title": title},
        ]
        self.make_query(expected, entry)

    def test_no_doi(self):
        title = "This is a title"
        authors = ["Alp", "Rom", "Bob"]
        # doi = "10.1234/123456"
        entry = {
            # "doi":doi,
            "author": " and ".join(authors),
            "title": title,
        }
        expected = [
            # {"doi":doi, "author": " ".join(authors), "title": title},
            {"doi": None, "author": " ".join(authors), "title": title},
            {"doi": None, "author": authors[0], "title": title},
            {"doi": None, "author": authors[1], "title": title},
            {"doi": None, "author": authors[2], "title": title},
            {"doi": None, "author": None, "title": title},
        ]
        self.make_query(expected, entry)

    def test_no_author(self):
        title = "This is a title"
        # authors = ["Alp", "Rom", "Bob"]
        doi = "10.1234/123456"
        entry = {
            "doi": doi,
            # "author": " and ".join(authors),
            "title": title,
        }
        expected = [
            {"doi": doi, "author": None, "title": title},
            # {"doi":None, "author": " ".join(authors), "title": title},
            # {"doi":None, "author": authors[0], "title": title},
            # {"doi":None, "author": authors[1], "title": title},
            # {"doi":None, "author": authors[2], "title": title},
            {"doi": None, "author": None, "title": title},
        ]
        self.make_query(expected, entry)

    def test_no_title(self):
        # title = "This is a title"
        authors = ["Alp", "Rom", "Bob"]
        doi = "10.1234/123456"
        entry = {
            "doi": doi,
            "author": " and ".join(authors),
            # "title": title
        }
        expected = [
            {"doi": doi, "author": " ".join(authors), "title": None},
            # {"doi":None, "author": " ".join(authors), "title": title},
            # {"doi":None, "author": authors[0], "title": title},
            # {"doi":None, "author": authors[1], "title": title},
            # {"doi":None, "author": authors[2], "title": title},
            # {"doi":None, "author": None, "title": title},
        ]
        self.make_query(expected, entry)

    def test_no_doi_author(self):
        title = "This is a title"
        # authors = ["Alp", "Rom", "Bob"]
        # doi = "10.1234/123456"
        entry = {
            # "doi":doi,
            # "author": " and ".join(authors),
            "title": title
        }
        expected = [
            # {"doi":doi, "author": " ".join(authors), "title": None},
            # {"doi":None, "author": " ".join(authors), "title": title},
            # {"doi":None, "author": authors[0], "title": title},
            # {"doi":None, "author": authors[1], "title": title},
            # {"doi":None, "author": authors[2], "title": title},
            {"doi": None, "author": None, "title": title},
        ]
        self.make_query(expected, entry)


class TestDTQuery:
    class parent(DTQueryMixin, SearchEval):
        def __repr__(self):
            return f"<doi:{self.doi}; title:{self.title}>"

    def make_query(self, expected, entry):
        p = self.parent(BibtexEntry(entry))
        p.index = 0
        p.expected = expected
        assert p.query() is None
        assert p.index == len(p.expected)

    def test_empty(self):
        self.make_query([], {})

    def test_all(self):
        title = "This is a title"
        doi = "10.1234/123456"
        entry = {"doi": doi, "title": title}
        expected = [
            {"doi": doi, "title": title},
            {"doi": None, "title": title},
        ]
        self.make_query(expected, entry)

    def test_no_doi(self):
        title = "This is a title"
        # doi = "10.1234/123456"
        entry = {
            # "doi":doi,
            "title": title,
        }
        expected = [
            # {"doi":doi, "title": title},
            {"doi": None, "title": title},
        ]
        self.make_query(expected, entry)

    def test_no_title(self):
        # title = "This is a title"
        doi = "10.1234/123456"
        entry = {
            "doi": doi,
            # "title": title
        }
        expected = [
            {"doi": doi, "title": None},
            # {"doi":None, "title": title},
        ]
        self.make_query(expected, entry)
