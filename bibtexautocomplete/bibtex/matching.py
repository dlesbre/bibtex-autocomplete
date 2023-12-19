"""
Function to determine how likely two entries are the same
"""

from typing import Set, Tuple

from .entry import BibtexEntry
from .normalize import normalize_str, normalize_str_weak, normalize_year

CERTAIN_MATCH = 1000  # Any score above is certain
NO_MATCH = 0  # Any score below is no match

# Matching score, XOR-ed together to get final score
# Higher score = more likely to match

# Added if DOIs match
MATCH_DOI = CERTAIN_MATCH

# Added if title match (after normalization)
MATCH_TITLE = CERTAIN_MATCH // 2
MATCH_TITLE_WEAK = CERTAIN_MATCH // 4  # uses a stronger normalization algorithm

# Full author list match,
MATCH_AUTHORS_FULL = CERTAIN_MATCH // 2
MATCH_AUTHORS_INCLUDED = CERTAIN_MATCH // 4  # A.authors included in B.authors or B in A
MATCH_AUTHORS_INTERSECTS = CERTAIN_MATCH // 8  # Non-empty intersection

# source.year == query.year
MATCH_YEAR = CERTAIN_MATCH // 4


def author_set(entry: BibtexEntry) -> Set[str]:
    """Returns the set of normalized author lastname from entry
    I.E. lowercase loast names, with spaces removed"""
    authors = entry.author
    last_names: Set[str] = set()
    for author in authors:
        normalized = normalize_str(author.lastname).replace(" ", "")
        if normalized != "":
            last_names.add(normalized)
    return last_names


def common_authors(a: BibtexEntry, b: BibtexEntry) -> Tuple[int, int, int]:
    """Returns:
    - number of common authors;
    - number of authors of a only,
    - number of authors of b only"""
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
        return MATCH_DOI
    if a.title is not None and b.title is not None:
        # Title is our best identifier
        if normalize_str_weak(a.title) == normalize_str_weak(b.title):
            score = MATCH_TITLE
        elif normalize_str(a.title) == normalize_str(b.title):
            score = MATCH_TITLE_WEAK
        else:
            return NO_MATCH
        authors_common, authors_a, authors_b = common_authors(a, b)
        if authors_common == 0 and authors_a > 0 and authors_b > 0:
            # No common authors despite some authors being known on both sides
            return NO_MATCH
        if authors_common != 0:
            if authors_common == authors_a and authors_common == authors_b:
                score += MATCH_AUTHORS_FULL
            elif authors_common == authors_a or authors_common == authors_b:
                score += MATCH_AUTHORS_INCLUDED
            else:
                score += MATCH_AUTHORS_INTERSECTS
        if a.year is not None and b.year is not None:
            a_year = normalize_year(a.year)
            b_year = normalize_year(b.year)
            if a_year is not None and b_year is not None:
                if a_year != b_year:
                    # Different years
                    return NO_MATCH
                score += MATCH_YEAR
        # Could check additional fields here
        return score
    return NO_MATCH
