from threading import Condition, Thread
from typing import Callable, Dict, List, Optional, Tuple

from ..bibtex.entry import BibtexEntry
from ..lookups.abstract_base import LookupType
from ..utils.constants import EntryType
from ..utils.logger import logger
from ..utils.safe_json import JSONType


class LookupThread(Thread):
    """As we our I/O limited,
    we can use threads to perform queries
    We create one thread per lookup, to keep query rate polite for each domain"""

    lookup: LookupType
    entries: List[EntryType] = []  # Read only
    condition: Condition
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
        entries: List[EntryType],
        condition: Condition,
        bar: Callable[[], None],
    ):
        self.entries = entries
        self.lookup = lookup
        self.condition = condition
        self.position = 0
        self.nb_entries = len(entries)
        self.result = []

        self.bar = bar
        super().__init__(name=lookup.name, daemon=True)

    def run(self) -> None:
        """Starts querying for entries"""
        logger.verbose_debug("Starting thread {name}", name=self.name)
        self.condition.acquire()
        while self.position < self.nb_entries:
            lookup = self.lookup(BibtexEntry(self.entries[self.position]))
            self.condition.release()

            result = lookup.query()

            self.condition.acquire()
            self.result.append((result, lookup.get_last_query_info()))
            self.position += 1
            self.bar()
            self.condition.notify()
        self.condition.release()
        return None
