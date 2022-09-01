"""
Project-wide constants
"""

from typing import Dict

NAME = "bibtexautocomplete"
SCRIPT_NAME = "btac"
AUTHOR = "Dorian Lesbre"
URL = "https://github.com/dlesbre/bibtex-autocomplete"
LICENSE = "MIT"
DESCRIPTION = "Module to complete bibtex files by polling online databases"

VERSION_MAJOR = 1
VERSION_MINOR = 1
VERSION_PATCH = 3

VERSION_DATE = "2022-08-13"

VERSION = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
VERSION_STR = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"

EMAIL = "dorian.lesbre" + chr(64) + "gmail.com"

# Minimum delay between queries to same host, to avoid surcharging server
MIN_QUERY_DELAY = 0.02  # s, so 50 per second
CONNECTION_TIMEOUT = 10.0  # seconds

USER_AGENT = f"{NAME}/{VERSION_STR} ({URL}; mailto:{EMAIL})"

EntryType = Dict[str, str]  # Type of a bibtex entry

MAX_THREAD_NB = 8  # Max number of threads

# Renaming pattern for nex files
# name is the filename, without extension ("ex" for "ex.bib")
# suffix is the file extansion, with leading dot (".bib" for "ex.bib")
BTAC_FILENAME = "{name}.btac{suffix}"

# Most APIs allow to limit the number of results returned for a search query
# This allows for smaller data transfers
QUERY_MAX_RESULTS = 3

# Prefix added to fields with -p / --prefix option
FIELD_PREFIX = "BTAC"
