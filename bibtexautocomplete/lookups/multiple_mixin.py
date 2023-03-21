"""
Mixin to perform multiple queries according to entry information
Set class attribute to be used by the query in get_data
"""

from typing import Iterator, Optional

from ..bibtex.entry import BibtexEntry
from ..bibtex.normalize import normalize_str
from .abstract_base import AbstractEntryLookup, AbstractLookup, Input, Output


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


class DOIQueryMixin(MultipleQueryMixin[BibtexEntry, BibtexEntry], AbstractEntryLookup):
    """Performs one query setting self.doi if self.entry has a doi
    then parent queries if any
    """

    doi: Optional[str] = None

    def iter_queries(self) -> Iterator[None]:
        self.doi = self.entry.doi
        if self.doi is not None:
            yield None
        # Perform more queries without doi
        self.doi = None
        for x in super().iter_queries():
            yield x


class TitleQueryMixin(
    MultipleQueryMixin[BibtexEntry, BibtexEntry], AbstractEntryLookup
):
    """Sets self.title if self.entry has a title
    Performs parent queries if any
    then perform a single query if self.title is set
    """

    title: Optional[str] = None

    def iter_queries(self) -> Iterator[None]:
        self.title = self.entry.title
        # Perform parent queries with title set
        for x in super().iter_queries():
            yield x
        if self.title is not None:
            yield None


class TitleAuthorQueryMixin(
    MultipleQueryMixin[BibtexEntry, BibtexEntry], AbstractEntryLookup
):
    """
    Sets self.title to entry title if any
    Sets self.author if self.entry has a authors to space separated list of lastnames
    Performs parent queries if any
    if self.title:
      performs a single query if self.author is not None
      performs a query per author
        (resetting self.author to just one author)
        if more than one author and self.single_author_queries is set
      unset self.author
      performs a single query
    """

    entry: BibtexEntry
    author_join: str = " "
    single_author_queries: bool = True
    title: Optional[str] = None
    author: Optional[str] = None

    max_author_queries: int = 10

    def iter_queries(self) -> Iterator[None]:
        # Find and format authors
        self.title = (
            None if self.entry.title is None else normalize_str(self.entry.title)
        )
        authors = self.entry.author
        if authors:
            self.author = self.author_join.join(author.lastname for author in authors)
        # Perform parent queries
        for x in super().iter_queries():
            yield x
        if self.title is None:
            return None
        # Perform one query with all authors
        yield None
        if len(authors) > 1 and self.single_author_queries:
            for ii, author in enumerate(authors):
                # Perform one query per author, with at most 10 queries
                if ii > self.max_author_queries:
                    break
                self.author = author.lastname
                yield None
        self.author = None
        if authors:
            yield None


class DATQueryMixin(TitleAuthorQueryMixin, DOIQueryMixin):
    """DOI - Authors - Title Mixin
    queries in order:
    - if doi, with doi, with title (if any), with all authors (if any)
    - if authors, with all authors, with title (if any)
    - if authors, with each author individually, with title (if any)
    - if title, with title (if any)"""

    pass


class DTQueryMixin(TitleQueryMixin, DOIQueryMixin):
    """DOI - Title Mixin
    queries in order:
    - if doi, with doi, with title (if any)
    - if title, with title (if any)"""

    pass
