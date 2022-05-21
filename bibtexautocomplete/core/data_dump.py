from typing import Any, Dict, Optional

from ..bibtex.entry import BibtexEntry


class DataDump:
    """Contains fields for all entries"""

    results: Dict[str, Optional[Dict[str, str]]]
    id: str
    new_fields: int

    def __init__(self, id: str) -> None:
        self.id = id
        self.new_fields = 0
        self.results = {}

    def add_entry(self, lookup_name: str, entry: Optional[BibtexEntry]) -> None:
        values = (
            {key: val for key, val in entry._entry.items() if val is not None}
            if entry is not None
            else None
        )
        self.results[lookup_name] = values

    def to_dict(self) -> Dict[str, Any]:
        json: Dict[str, Any] = {
            "entry": self.id,
            "new-fields": self.new_fields,
        }
        json.update(self.results)
        return json
