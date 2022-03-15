"""
Project-wide constants
"""


NAME = "bibtexautocomplete"
AUTHOR = "Dorian Lesbre"
URL = "https://github.com/dlesbre/bibtex-autocomplete"
LICENSE = "MIT"

VERSION_MAJOR = 0
VERSION_MINOR = 4
VERSION_PATCH = 0

VERSION = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
VERSION_STR = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"

EMAIL = "dorian.lesbre" + chr(64) + "gmail.com"

CONNECTION_TIMEOUT = 10.0  # seconds

USER_AGENT = f"{NAME}/{VERSION_STR} ({URL}; mailto:{EMAIL})"

EntryType = dict[str, str]  # Type of a bibtex entry
