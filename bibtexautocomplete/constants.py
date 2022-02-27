from typing import Dict

from Levenshtein import ratio  # type: ignore

NAME = "bibtexautocomplete"
VERSION = "0.1.0"
URL = "https://github.com/dlesbre/bibtex-autocomplete"
LICENSE = "MIT"

USER_AGENT = f"{NAME}/{VERSION} ({URL})"

EntryType = Dict[str, str]  # Type of a bibtex entry


def str_similar(s1: str, s2: str) -> bool:
    """Check string similarity (Levenshtein ratio > 0.95)"""
    return ratio(s1, s2) >= 0.95
