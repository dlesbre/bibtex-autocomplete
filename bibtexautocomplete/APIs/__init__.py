from typing import List

from ..lookups.abstract_base import LookupType
from .arxiv import ArxivLookup
from .crossref import CrossrefLookup
from .dblp import DBLPLookup
from .openalex import OpenAlexLookup
from .researchr import ResearchrLookup
from .semantic_scholar import SemanticScholarLookup
from .unpaywall import UnpaywallLookup

# List of lookup to use, in the order they will be used
LOOKUPS: List[LookupType] = [
    OpenAlexLookup,
    CrossrefLookup,
    ArxivLookup,
    SemanticScholarLookup,
    DBLPLookup,
    ResearchrLookup,
    UnpaywallLookup,
]
LOOKUP_NAMES = [cls.name for cls in LOOKUPS]

__all__ = (
    "LookupType",
    "LOOKUPS",
    "LOOKUP_NAMES",
    "OpenAlexLookup",
    "CrossrefLookup",
    "SemanticScholarLookup",
    "ArxivLookup",
    "DBLPLookup",
    "ResearchrLookup",
    "UnpaywallLookup",
)
