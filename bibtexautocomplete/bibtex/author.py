"""
A class to represent author/editor names and read/write them to valid bibtex
"""

from typing import Optional

AUTHOR_JOIN = " and "


class Author:
    firstnames: Optional[str]
    lastname: str

    def __init__(self, lastname: str, firstnames: Optional[str]) -> None:
        self.lastname = lastname
        self.firstnames = firstnames

    def __repr__(self) -> str:
        return f"Author({self.lastname}, {self.firstnames})"

    def to_bibtex(self) -> str:
        """Returns a bibtex representation of self:
        lastname, firstname"""
        if self.firstnames is not None:
            return f"{self.lastname}, {self.firstnames}"
        return self.lastname

    @staticmethod
    def list_to_bibtex(authors: "list[Author]") -> str:
        return AUTHOR_JOIN.join(author.to_bibtex() for author in authors)

    def __eq__(self, other) -> bool:
        "Used in test only"
        return self.firstnames == other.firstnames and self.lastname == other.lastname

    @staticmethod
    def from_name(name: Optional[str]) -> "Optional[Author]":
        """Reads a bibtex string into a author name"""
        if name is None or name == "" or name.isspace():
            return None
        name = name.replace("\n", "").strip()
        if "," in name:
            namesplit = name.split(",", 1)
            last = namesplit[0].strip()
            firsts = [i.strip() for i in namesplit[1].split()]
        else:
            namesplit = name.split()
            last = namesplit.pop()
            firsts = [i.replace(".", ". ").strip() for i in namesplit]
        if last in ["jnr", "jr", "junior"]:
            last = firsts.pop()
        for item in firsts:
            if item in ["ben", "van", "der", "de", "la", "le"]:
                last = firsts.pop() + " " + last
        first = " ".join(firsts) if firsts else None
        return Author(last, first)

    @classmethod
    def from_namelist(cls, authors: str) -> "list[Author]":
        """Return a list of 'first name', 'last name' for authors"""
        result = []
        for name in authors.replace("\n", " ").replace("\t", " ").split(AUTHOR_JOIN):
            aut = cls.from_name(name)
            if aut is not None:
                result.append(aut)
        return result
