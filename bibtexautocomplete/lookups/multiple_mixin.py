"""
Mixin to perform multiple queries according to entry information
Set class attribute to be used by the query in get_data
"""

from typing import Iterator, List, Optional

from ..bibtex.entry import BibtexEntry
from ..bibtex.normalize import normalize_str
from .abstract_base import AbstractLookup, Input, Output
from .abstract_entry_lookup import AbstractEntryLookup


class MultipleQueryMixin(AbstractLookup[Input, Output]):
    """Mixin to perform multiple queries

    Defines:
    - iter_queries : Self -> Iterator[None] - empty iterator (should be overridden)
    - query : Self -> Optional[BibtexEntry] - call parent query as long as iter_query yields
        stop a first valid (non None) value
    """

    def iter_queries(self) -> Iterator[None]:
        """Used to iterate through the queries
        The yielded result doesn't really matter.
        This method should dynamically modify attributes (like self.title)
        which are then used when constructing queries (i.e. in get_param())
        Default behavior: no queries"""
        return iter([])

    def query(self) -> Optional[Output]:
        """Performs queries as long as iter_query yields
        Stops at first valid result found"""
        for _ in self.iter_queries():
            value = super().query()
            if value is not None:
                return value
        return None


class DAT_Query_Mixin(MultipleQueryMixin[BibtexEntry, BibtexEntry], AbstractEntryLookup):
    """Performs queries using
    - the entry's DOI if it is known and if query_doi is True
    - the entry's title and author if known and if query_author_title is True
    - the entry's title if known and if query_title is True
    Using here means the fields self.doi is set before the query
    """

    # Use these to select which queries to perform
    query_doi: bool = True
    query_author_title: bool = True
    query_title: bool = True

    # Use these to obtain the data when making queries
    doi: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[List[str]] = None

    def iter_queries(self) -> Iterator[None]:
        self.title = self.entry.title.to_str()
        if self.title is not None:
            self.title = normalize_str(self.title)
        self.doi = self.entry.doi.to_str()
        authors = self.entry.author.value
        if authors is not None:
            self.authors = [author.lastname for author in authors]

        if self.query_doi and self.doi is not None:
            yield None
            self.doi = None

        if self.title is None:
            return

        if self.query_author_title and self.authors is not None:
            yield None
            self.authors = None

        if self.query_title:
            yield None
