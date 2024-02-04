from typing import Any, Dict, Optional

from ..bibtex.constants import FieldNamesSet
from ..bibtex.entry import BibtexEntry
from ..utils.safe_json import JSONType


class DataDump:
    """Contains fields for all entries"""

    results: Dict[str, Optional[Dict[str, JSONType]]]
    id: str
    new_fields: int

    def __init__(self, id: str) -> None:
        self.id = id
        self.new_fields = 0
        self.results = {}

    def add_entry(
        self, lookup_name: str, entry: Optional[BibtexEntry], info: Dict[str, JSONType]
    ) -> None:
        if entry is None:
            self.results[lookup_name] = None
            return
        infos = {"query-" + key: val for key, val in info.items()}
        for key in FieldNamesSet:
            field = entry.get_field(key).to_str()
            if field is not None:
                infos[key] = field
        self.results[lookup_name] = infos

    def to_dict(self) -> Dict[str, Any]:
        json: Dict[str, Any] = {
            "entry": self.id,
            "new-fields": self.new_fields,
        }
        json.update(self.results)
        return json
