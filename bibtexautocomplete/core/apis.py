from typing import List

from ..APIs.arxiv import ArxivLookup
from ..APIs.crossref import CrossrefLookup
from ..APIs.dblp import DBLPLookup
from ..APIs.inspire_hep import InpireHEPLookup
from ..APIs.openalex import OpenAlexLookup
from ..APIs.researchr import ResearchrLookup
from ..APIs.semantic_scholar import SemanticScholarLookup
from ..APIs.unpaywall import UnpaywallLookup
from ..lookups.abstract_base import LookupType

# List of lookup to use, in the order they will be used
LOOKUPS: List[LookupType] = [
    OpenAlexLookup,
    CrossrefLookup,
    ArxivLookup,
    SemanticScholarLookup,
    UnpaywallLookup,
    DBLPLookup,
    ResearchrLookup,
    InpireHEPLookup,
]
LOOKUP_NAMES = [cls.name for cls in LOOKUPS]
