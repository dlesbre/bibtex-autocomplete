"""
Function to determine how likely two entries are the same
"""

from .entry import BibtexEntry
from .normalize import normalize_str, normalize_str_weak

ENTRY_CERTAIN_MATCH = 1000  # Maximum score
ENTRY_NO_MATCH = 0  # Minimum score


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
            score = ENTRY_CERTAIN_MATCH * 2 // 3
        elif normalize_str(a.title) == normalize_str(b.title):
            score = ENTRY_CERTAIN_MATCH // 3
        else:
            return ENTRY_NO_MATCH
        # Could check additional fields here
        return score
    return ENTRY_NO_MATCH
