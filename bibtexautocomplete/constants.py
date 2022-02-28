import logging
from typing import Dict

# =====================================================
# Constants
# =====================================================

NAME = "bibtexautocomplete"
VERSION = "0.1"
URL = "https://github.com/dlesbre/bibtex-autocomplete"
LICENSE = "MIT"

EMAIL = "dorian.lesbre" + chr(64) + "gmail.com"

CONNECTION_TIMEOUT = 10.0  # seconds

USER_AGENT = f"{NAME}/{VERSION} ({URL}; mailto:{EMAIL})"

EntryType = Dict[str, str]  # Type of a bibtex entry

# =====================================================
# Logger
# =====================================================

# create logger
logger = logging.getLogger(NAME)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

# =====================================================
# Utility functions
# =====================================================


def str_normalize(s1: str) -> str:
    """Normalize string for decent comparison"""
    res = ""
    prev_space = False
    for x in s1:
        if x.isalnum():
            res += x
            prev_space = False
        elif not prev_space:
            res += " "
            prev_space = True
    return res.lower().strip()


def str_similar(s1: str, s2: str) -> bool:
    """String equality, case insensitive"""
    return str_normalize(s1) == str_normalize(s2)
