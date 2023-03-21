"""
Project-wide constants
"""

from typing import Dict

NAME = "bibtexautocomplete"
SCRIPT_NAME = "btac"
AUTHOR = "Dorian Lesbre"
URL = "https://github.com/dlesbre/bibtex-autocomplete"
ISSUES_URL = URL + "/issues"
LICENSE = "MIT"
DESCRIPTION = "Module to complete bibtex files by polling online databases"

VERSION_MAJOR = 1
VERSION_MINOR = 1
VERSION_PATCH = 8

VERSION_DATE = "2023-02-27"

VERSION = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
VERSION_STR = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"

EMAIL = "dorian.lesbre" + chr(64) + "gmail.com"

# Minimum delay between queries to same host, to avoid surcharging server
MIN_QUERY_DELAY = 0.02  # s, so 50 per second
CONNECTION_TIMEOUT = 20.0  # seconds

USER_AGENT = f"{NAME}/{VERSION_STR} ({URL}; mailto:{EMAIL})"

EntryType = Dict[str, str]  # Type of a bibtex entry

MAX_THREAD_NB = 8  # Max number of threads

# Renaming pattern for nex files
# name is the filename, without extension ("ex" for "ex.bib")
# suffix is the file extansion, with leading dot (".bib" for "ex.bib")
BTAC_FILENAME = "{name}.btac{suffix}"

# Most APIs allow to limit the number of results returned for a search query
# This allows for smaller data transfers
QUERY_MAX_RESULTS = 10

# Prefix added to fields with -p / --prefix option
FIELD_PREFIX = "BTAC"

# Field used to mark entries, the value is mostly irrelevant
# As only field presence is tested
MARKED_FIELD = FIELD_PREFIX + "queried"

# Bullet printed to the screen when printing a list
BULLET = "{FgBlue}{StBold}*{Reset} "
