from datetime import datetime
from os import path
from typing import Iterable, List, Optional, Tuple

import pytest

from bibtexautocomplete.bibtex.constants import FieldNames
from bibtexautocomplete.bibtex.entry import BibtexEntry
from bibtexautocomplete.core.apis import LOOKUPS
from bibtexautocomplete.core.main import main
from bibtexautocomplete.lookups.abstract_base import AbstractDataLookup, Data
from bibtexautocomplete.lookups.search_mixin import EntryMatchSearchMixin
from bibtexautocomplete.utils.safe_json import SafeJSON

# Parent directory of this file
base_dir = path.abspath(path.dirname(__file__))
test_dir = path.join(base_dir, "bibs")
input_bib = path.join(test_dir, "input.bib")


# Set to true to replace the exp files by those generated by the tests
PROMOTE = False


class FakeLookup(EntryMatchSearchMixin[SafeJSON], AbstractDataLookup[BibtexEntry, BibtexEntry]):
    """A fake lookup, complete entries with deterministic info
    Used in test to avoid needlessly querying APIs"""

    name = "fake_lookup"
    count: int = 0
    fields = {
        FieldNames.TITLE,
        FieldNames.AUTHOR,
        FieldNames.BOOKTITLE,
        FieldNames.JOURNAL,
        FieldNames.MONTH,
        FieldNames.PAGES,
        FieldNames.ORGANIZATION,
        FieldNames.VOLUME,
        FieldNames.NOTE,
        FieldNames.EDITION,
        FieldNames.ISSN,
    }

    def get_data(self) -> Optional[Data]:
        """Dummy data"""
        return Data(
            data=bytes("1234", "utf8"),
            code=200,
            delay=1.0,
            reason="ok",
        )

    def get_results(self, data: bytes) -> Optional[Iterable[SafeJSON]]:
        """Dummy results"""
        FakeLookup.count += 1
        return [SafeJSON(FakeLookup.count)]

    def get_value(self, res: SafeJSON) -> BibtexEntry:
        """Return the relevant value (e.g. updated entry)"""
        entry = BibtexEntry(self.name, self.entry.id)
        count = res.to_int()
        if count is None:
            raise ValueError()
        # Add basic defaults
        entry.title.set(f"Generated title {count}")
        entry.author.set_str(f"John Doe{count}")
        entry.booktitle.set(f"Generated booktitle {count}")
        # entry.doi.set(f"10.00000/generated.{count}")
        entry.journal.set_str(f"Generated Journal {count}")
        entry.month.set(str(count % 12 + 1))
        entry.pages.set_str(f"1 -- {count}")
        entry.organization.set_str(f"organization {count}")
        entry.volume.set_str(str(count))
        entry.note.set(f"Note: this is query number {count}")
        entry.edition.set(f"Edition {count}")
        entry.issn.set_str(f"{str(count).zfill(4)}-0001")
        # entry.url.set("https://example.com/")

        # Cheekily copy fields from the source entry
        present_fields = self.entry.fields()
        present_fields.discard(FieldNames.JOURNAL)
        for field in present_fields:
            entry.get_field(field).set(self.entry.get_field(field).value)

        return entry


LOOKUPS.clear()
LOOKUPS.append(FakeLookup)

# List of pairs:
# - args to pass to main (argv from the command line)
# - files to compare afterwards (expected first)
tests: List[Tuple[List[str], List[Tuple[str, str]]]] = [
    # Tests for options which match their default values
    ([input_bib], [("input.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "-o", path.join(test_dir, "input.btac.bib")], [("input.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "-o", path.join(test_dir, "output.btac.bib")], [("input.btac.bib.exp", "output.btac.bib")]),
    ([input_bib, "--output", path.join(test_dir, "input.btac.bib")], [("input.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--output=" + path.join(test_dir, "foo.btac.bib")], [("input.btac.bib.exp", "foo.btac.bib")]),
    ([input_bib, "--fi", "t"], [("input.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--fi", "\t"], [("input.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "-C", "address", "-C", "editor"], [("input.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "-C", "address", "--dont-complete=editor"], [("input.btac.bib.exp", "input.btac.bib")]),
    (
        [
            input_bib,
            "-c",
            "title",
            "-c=author",
            "--only-complete",
            "booktitle",
            "-c=journal",
            "--only-complete=month",
            "-c=pages",
            "-c=organization",
            "-c=volume",
            "-c=note",
            "-c=edition",
            "-c=issn",
        ],
        [("input.btac.bib.exp", "input.btac.bib")],
    ),
    (
        [
            input_bib,
            "-c",
            "title",
            "-c=author",
            "--only-complete",
            "booktitle",
            "-c=journal",
            "--only-complete=month",
            "-c=pages",
            "-c=organization",
            "-c=volume",
            "-c=note",
            "-c=edition",
            "-c=issn",
            "-C",
            "author",
            "--fi=t",
        ],
        [("input.btac.bib.exp", "input.btac.bib")],
    ),
    # Formatting tests
    ([input_bib, "--fi", "  "], [("format-space.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--indent", "  "], [("format-space.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--fi=2"], [("format-space.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--fi=__"], [("format-space.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--fi", " _\n\t"], [("format-space2.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--indent", "__nt"], [("format-space2.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--fl"], [("format-comma.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--no-trailing-comma"], [("format-comma.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--fc"], [("format-leading.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--comma-first"], [("format-leading.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--fa"], [("format-align.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--align-values"], [("format-align.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--fa", "--fc", "--fl", "--fi=  \t"], [("format-all.btac.bib.exp", "input.btac.bib")]),
    # Prefix and marked tests
    ([input_bib, "-p"], [("prefix.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--prefix"], [("prefix.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "-M"], [("mark-ignore.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--ignore-mark"], [("mark-ignore.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "-m"], [("mark.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--mark"], [("mark.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--mark", "--prefix"], [("mark-prefix.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "-f"], [("overwrite.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "--force-overwrite"], [("overwrite.btac.bib.exp", "input.btac.bib")]),
    ([input_bib, "-fp"], [("overwrite-prefix.btac.bib.exp", "input.btac.bib")]),
]


@pytest.mark.parametrize(("argv", "files_to_compare"), tests)
def test_main(argv: List[str], files_to_compare: List[Tuple[str, str]]) -> None:
    main(argv)
    FakeLookup.count = 0
    day = datetime.today().strftime("%Y-%m-%d")
    for expected, generated in files_to_compare:
        with open(path.join(test_dir, generated), "r") as generated_file:
            generated_contents = generated_file.read()
        if PROMOTE:
            with open(path.join(test_dir, expected), "w") as expected_file:
                expected_file.write(generated_contents.replace(day, "DATE"))
        else:
            with open(path.join(test_dir, expected), "r") as expected_file:
                expected_contents = expected_file.read().replace("DATE", day)
            assert expected_contents == generated_contents
