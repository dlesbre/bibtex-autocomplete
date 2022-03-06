from typing import Optional

from bibtexautocomplete.bibtex.entry import BibtexEntry, FieldNames
from bibtexautocomplete.lookups.abstract_base import AbstractLookup
from bibtexautocomplete.lookups.condition_mixin import FieldConditionMixin
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


class ConditionEval(AbstractLookup):
    queried: bool

    def __init__(self, entry: BibtexEntry):
        self.queried = False
        super().__init__(entry)

    def query(self):
        self.queried = True
        return None


class TestCondition:
    class parent(FieldConditionMixin, ConditionEval):
        fields = {
            FieldNames.DOI,
            FieldNames.TITLE,
            FieldNames.AUTHOR,
        }

    def run(self, entry: dict[str, str], expected: bool):
        p = self.parent(BibtexEntry(entry))
        p.query()
        assert p.queried == expected

    def test_empty(self):
        self.run({}, True)
        self.run({"junk": "junk", "more junk": "more junk"}, True)

    def test_full(self):
        self.run(
            {"doi": "10.1234/1234", "title": "A Title", "author": "John Jones"}, False
        )

    def test_partial(self):
        self.run(
            {
                # "doi":"10.1234/1234",
                "title": "A Title",
                "author": "John Jones",
            },
            True,
        )
        self.run(
            {
                "doi": "10.1234/1234",
                # "title":"A Title",
                "author": "John Jones",
            },
            True,
        )
        self.run(
            {
                "doi": "10.1234/1234",
                "title": "A Title",
                # "author":"John Jones"
            },
            True,
        )

    def test_invalid(self):
        self.run({"doi": "", "title": "A Title", "author": "John Jones"}, True)
        self.run({"doi": "10.1234/1234", "title": "A Title", "author": "{}"}, True)
        self.run(
            {"doi": "10.1234/1234", "title": "A Title", "author": "{{}{{}}}"}, True
        )

    def test_filter(self):
        old = self.parent.fields_to_complete
        self.parent.fields_to_complete = {
            FieldNames.DOI,
        }
        self.run(
            {
                # "doi":"10.1234/1234",
                "title": "A Title",
                "author": "John Jones",
            },
            True,
        )
        self.run(
            {
                "doi": "10.1234/1234",
                # "title":"A Title",
                "author": "John Jones",
            },
            False,
        )
        self.run(
            {
                "doi": "10.1234/1234",
                "title": "A Title",
                # "author":"John Jones"
            },
            False,
        )
        self.parent.fields_to_complete = old
