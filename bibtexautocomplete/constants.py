from typing import Dict

NAME = "bibtexautocomplete"
VERSION = "0.1"
URL = "https://github.com/dlesbre/bibtex-autocomplete"
LICENSE = "MIT"

EMAIL = "dorian.lesbre" + chr(64) + "gmail.com"

CONNECTION_TIMEOUT = 5.0  # seconds

USER_AGENT = f"{NAME}/{VERSION} ({URL}; mailto:{EMAIL})"

EntryType = Dict[str, str]  # Type of a bibtex entry


def str_similar(s1: str, s2: str) -> bool:
    """String equality, case insensitive"""
    return s1.lower().strip().replace("  ", " ") == s2.lower().strip().replace(
        "  ", " "
    )
