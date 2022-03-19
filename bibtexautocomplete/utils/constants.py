"""
Project-wide constants
"""


NAME = "bibtexautocomplete"
SCRIPT_NAME = "btac"
AUTHOR = "Dorian Lesbre"
URL = "https://github.com/dlesbre/bibtex-autocomplete"
LICENSE = "MIT"

VERSION_MAJOR = 0
VERSION_MINOR = 4
VERSION_PATCH = 0

VERSION = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
VERSION_STR = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"

EMAIL = "dorian.lesbre" + chr(64) + "gmail.com"

# Minimum delay between queries to same host, to avoid surcharging server
MIN_QUERY_DELAY = 0.02  # s, so 50 per second
CONNECTION_TIMEOUT = 10.0  # seconds

USER_AGENT = f"{NAME}/{VERSION_STR} ({URL}; mailto:{EMAIL})"

EntryType = dict[str, str]  # Type of a bibtex entry

MAX_THREAD_NB = 8  # Max number of threads

# Renaming pattern for nex files
# name is the filename, without extension ("ex" for "ex.bib")
# suffix is the file extansion, with leading dot (".bib" for "ex.bib")
BTAC_FILENAME = "{name}.btac{suffix}"
