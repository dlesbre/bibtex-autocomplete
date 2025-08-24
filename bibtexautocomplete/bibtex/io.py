"""
Wraps around bibtexparser to provider parser/writer primitives
"""

from typing import List, cast

from bibtexparser.bibdatabase import BibDatabase, UndefinedString
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter

from ..utils.constants import EntryType, PathType
from ..utils.functions import BTAC_File_Error
from ..utils.logger import logger

# from bibtexparser.customization import convert_to_unicode


def make_writer() -> BibTexWriter:
    writer = BibTexWriter()
    writer.indent = "\t"
    writer.add_trailing_comma = True
    writer.order_entries_by = None  # preserve order
    writer.display_order = ("title", "author")
    return writer


def write(database: BibDatabase, writer: BibTexWriter) -> str:
    """Transform the database to a bibtex string"""
    return cast(str, writer.write(database).strip() + "\n")


def read(bibtex: str, src: str = "") -> BibDatabase:
    """Parses bibtex string into database"""
    parser = BibTexParser(common_strings=True)
    # Keep non standard entries if present
    parser.ignore_nonstandard_types = False
    try:
        database = parser.parse(bibtex)
    except UndefinedString as err:
        src = " '" + src + "'" if src else ""
        logger.critical(
            "Failed to parse bibtex{src}: {FgPurple}undefined string{Reset} '{err}'",
            src=src,
            err=err,
        )
        raise BTAC_File_Error(
            "Failed to parse bibtex{src}: undefined string '{err}'".format(src=src, err=err), err
        ) from None
    return database


def file_write(filepath: PathType, database: BibDatabase, writer: BibTexWriter) -> bool:
    """Writes database to given file, stdout if None"""
    output = write(database, writer)
    if filepath is None:
        print(output)
        return True
    try:
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(output)
    except (IOError, UnicodeDecodeError) as err:
        logger.error(
            "Failed to write to '{filepath}' : {FgPurple}{err}{Reset}",
            filepath=str(filepath),
            err=err,
        )
        return False
    return True


def file_read(filepath: PathType) -> BibDatabase:
    """reads the given file, parses and normalizes it"""
    # Read and parse the file
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            bibtex = file.read()
    except (IOError, UnicodeDecodeError) as err:
        logger.critical(
            "Failed to read '{filepath}': {FgPurple}{err}{Reset}",
            filepath=str(filepath),
            err=err,
        )
        raise BTAC_File_Error(
            "Failed to read '{filepath}': {err}".format(filepath=str(filepath), err=err), err
        ) from None
    return read(bibtex, str(filepath))


def get_entries(db: BibDatabase) -> List[EntryType]:
    """Get entries from a bibdatabase"""
    return list(db.entries)
