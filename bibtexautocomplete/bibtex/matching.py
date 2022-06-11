"""
Function to determine how likely two entries are the same
"""

from typing import Set, Tuple

from .entry import BibtexEntry
from .normalize import normalize_str, normalize_str_weak

ENTRY_CERTAIN_MATCH = 1000  # Maximum score
ENTRY_NO_MATCH = 0  # Minimum score


def author_set(entry: BibtexEntry) -> Set[str]:
    """Returns the set of normalized author lastname from entry"""
    authors = entry.author
    last_names: Set[str] = set()
    for author in authors:
        normalized = normalize_str(author.lastname).replace(" ", "")
        if normalized != "":
            last_names.add(normalized)
    return last_names


def common_authors(a: BibtexEntry, b: BibtexEntry) -> Tuple[int, int, int]:
    """Returns:
    number of common authors, number of a authors, number of authors of b"""
    authors_a = author_set(a)
    authors_b = author_set(b)
    common = authors_a.intersection(authors_b)
    return len(common), len(authors_a), len(authors_b)


def match_score(a: BibtexEntry, b: BibtexEntry) -> int:
    """
    Assign a score between ENTRY_NO_MATCH and ENTRY_CERTAIN_MATCH (included)
    representing how likely two entries are to be matched
    """
    if a.doi is not None and a.doi == b.doi:
        # DOIs are unique => entries match
        return ENTRY_CERTAIN_MATCH
    if a.title is not None and b.title is not None:
        # Title is our best identifier
        if normalize_str_weak(a.title) == normalize_str_weak(b.title):
            score = ENTRY_CERTAIN_MATCH // 2
        elif normalize_str(a.title) == normalize_str(b.title):
            score = ENTRY_CERTAIN_MATCH // 3
        else:
            return ENTRY_NO_MATCH
        authors_common, authors_a, authors_b = common_authors(a, b)
        if authors_common == 0 and authors_a > 0 and authors_b > 0:
            # No common authors despite some authors being known on both sides
            return ENTRY_NO_MATCH
        if authors_common != 0:
            if authors_common == authors_a and authors_common == authors_b:
                score += ENTRY_CERTAIN_MATCH // 3
            elif authors_common == authors_a or authors_common == authors_b:
                score += ENTRY_CERTAIN_MATCH // 6
            else:
                score += ENTRY_CERTAIN_MATCH // 9
        # Could check additional fields here
        return score
    return ENTRY_NO_MATCH
