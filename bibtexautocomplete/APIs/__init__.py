from ..lookups.abstract_base import LookupType
from .crossref import CrossrefLookup
from .dblp import DBLPLookup
from .researchr import ResearchrLookup
from .unpaywall import UnpaywallLookup

# List of lookup to use, in the order they will be used
LOOKUPS: list[LookupType] = [
    CrossrefLookup,
    DBLPLookup,
    ResearchrLookup,
    UnpaywallLookup,
]
LOOKUP_NAMES = [cls.name for cls in LOOKUPS]

__all__ = ("LookupType", "LOOKUPS", "LOOKUP_NAMES")
