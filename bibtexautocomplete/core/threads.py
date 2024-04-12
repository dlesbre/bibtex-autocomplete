from threading import Condition, Thread
from typing import Callable, Dict, List, Optional, Set, Tuple

from ..bibtex.constants import FieldType
from ..bibtex.entry import BibtexEntry
from ..lookups.abstract_entry_lookup import LookupType
from ..utils.logger import logger
from ..utils.safe_json import JSONType


class LookupThread(Thread):
    """As we our I/O limited,
    we can use threads to perform queries
    We create one thread per lookup, to keep query rate polite for each domain"""

    lookup: LookupType
    entries: List[BibtexEntry] = []  # Read only
    to_complete: List[Set[FieldType]] = []  # Read only
    condition: Condition
    entry_name: Optional[str]
    result: List[
        Tuple[
            Optional[BibtexEntry],
            Dict[str, JSONType],
        ]
    ]  # Write

    position: int
    nb_entries: int

    def __init__(
        self,
        lookup: LookupType,
        entries: List[BibtexEntry],
        to_complete: List[Set[FieldType]],
        condition: Condition,
        bar: Callable[[], None],
    ):
        self.entries = entries
        self.to_complete = to_complete
        self.lookup = lookup
        self.condition = condition
        self.position = 0
        self.nb_entries = len(entries)
        self.result = []

        self.bar = bar
        super().__init__(name=lookup.name, daemon=True)

    def run(self) -> None:
        """Starts querying for entries"""
        logger.very_verbose_debug("Starting thread {name}", name=self.name)
        self.condition.acquire()
        while self.position < self.nb_entries:
            entry = self.entries[self.position]
            self.entry_name = entry.id
            lookup = self.lookup(entry)
            self.condition.release()

            if lookup.fields.isdisjoint(self.to_complete[self.position]):
                # Skip query as no fields need to be completed
                result = None
                info = dict()
                logger.debug("Skipping query, no data to add")
            else:
                try:
                    result = lookup.query()
                    info = lookup.get_last_query_info()
                except Exception as err:
                    result = None
                    info = lookup.get_last_query_info()
                    logger.traceback(
                        "Uncaught exception when trying to autocomplete entry\n"
                        f"Entry = {self.entry_name}\n"
                        f"Website = {self.name}",
                        err,
                    )

            self.condition.acquire()
            self.result.append((result, info))
            self.position += 1
            self.bar()
            self.condition.notify()
        self.condition.release()
        return None
