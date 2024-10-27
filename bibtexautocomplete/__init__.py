from .core.autocomplete import BibtexAutocomplete
from .core.main import main
from .utils.constants import AUTHOR, DESCRIPTION, EMAIL, URL, VERSION_STR

__author__ = AUTHOR
__email__ = EMAIL
__version__ = VERSION_STR
__url__ = URL

__description__ = DESCRIPTION


__all__ = ["main", "BibtexAutocomplete"]
