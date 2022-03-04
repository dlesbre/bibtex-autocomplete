from .core.autocomplete import BibtexAutocomplete
from .core.main import main
from .utils.constants import AUTHOR, EMAIL, VERSION_STR

__author__ = AUTHOR
__email__ = EMAIL
__version__ = VERSION_STR

__description__ = "Module to complete bibtex files by polling online databases"

__all__ = ("main", "BibtexAutocomplete")
