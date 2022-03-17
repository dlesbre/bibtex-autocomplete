"""
Wraps around bibtexparser to provider parser/writer primitives
"""

from bibtexparser.bibdatabase import BibDatabase, UndefinedString
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.customization import convert_to_unicode

from ..utils.constants import EntryType
from ..utils.logger import logger

parser = BibTexParser(common_strings=True)
# Keep non standard entries if present
parser.ignore_nonstandard_types = False

writer = BibTexWriter()
writer.indent = "\t"
writer.add_trailing_comma = True
writer.order_entries_by = ("author", "year", "title")
writer.display_order = ("author", "title")


def write(database: BibDatabase) -> str:
    """Transform the database to a bibtex string"""
    return writer.write(database).strip()


def read(bibtex: str, src: str = "") -> BibDatabase:
    """Parses bibtex string into database"""
    try:
        database = parser.parse(bibtex)
    except UndefinedString as err:
        src = " '" + src + "'" if src else ""
        logger.critical(
            "Failed to parse bibtex{src}: {FgPurple}undefined string{FgReset} '{err}'",
            src=src,
            err=err,
        )
        exit(1)
    for entry in database.entries:
        convert_to_unicode(entry)
    return database


def file_write(filepath, database: BibDatabase) -> bool:
    """Writes database to given file, stdout if None"""
    output = write(database)
    if filepath is None:
        print(output)
        return True
    try:
        with open(filepath, "w") as file:
            file.write(output)
    except IOError as err:
        logger.error(
            "Failed to write to '{filepath}' : {FgPurple}{err}{FgReset}",
            filepath=str(filepath),
            err=err,
        )
        return False
    return True


def file_read(filepath) -> BibDatabase:
    """reads the given file, parses and normalizes it"""
    # Read and parse the file
    try:
        with open(filepath, "r") as file:
            bibtex = file.read()
    except IOError as err:
        logger.critical(
            "Failed to read '{filepath}': {FgPurple}{err}{FgReset}",
            filepath=str(filepath),
            err=err,
        )
        exit(1)
    return read(bibtex)


def get_entries(db: BibDatabase) -> list[EntryType]:
    """Get entries from a bibdatabase"""
    return db.entries
