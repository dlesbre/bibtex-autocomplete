"""
A class for parsing JSON data without checking structure every time
No operations will raise any error, invalid operations will simply return None
"""


from json import JSONDecodeError, JSONDecoder
from typing import Any, Dict, Iterator, List, Optional, Tuple, TypeVar, Union

JSONType = Union[Dict[str, Any], List[Any], int, float, str, bool, None]
S = TypeVar("S", bound=JSONType)


class SafeJSON:
    """class designed to make failess accesses to a JSON-like structure
    (recursive structure of either Dict[str, SafeJSON], List[SafeJSON], int, float, str, bool, None)

    defines get_item to seamlessly access dict entries (if item is str) or list element (if item is int)
    """

    value: JSONType

    def __init__(self, value: JSONType) -> None:
        self.value = value

    def __getitem__(self, key: Union[int, str]) -> "SafeJSON":
        result: JSONType = None
        if isinstance(key, int):
            if key >= 0 and isinstance(self.value, list) and len(self.value) > key:
                result = self.value[key]
        else:
            if isinstance(self.value, dict):
                result = self.value.get(key)
        return SafeJSON(result)

    @staticmethod
    def from_str(json: str) -> "SafeJSON":
        """Parses a json string into SafeJSON, returns SafeJSON(None) if invalid string"""
        try:
            decoded = JSONDecoder().decode(json)
        except JSONDecodeError:
            return SafeJSON(None)  # empty
        return SafeJSON(decoded)

    @staticmethod
    def from_bytes(json: bytes) -> "SafeJSON":
        """Parses a json bytes string into SafeJSON, returns SafeJSON(None) if invalid string"""
        return SafeJSON.from_str(json.decode())

    def dict_contains(self, key: str) -> bool:
        """Returns true if self is a dict and has the given key"""
        if isinstance(self.value, dict):
            return key in self.value
        return False

    def to_str(self) -> Optional[str]:
        """Returns the value if it is an str, None otherwise"""
        if isinstance(self.value, str):
            return self.value
        return None

    def force_str(self) -> Optional[str]:
        """Returns str(value) if valus is str, int, float or bool"""
        if isinstance(self.value, (str, int, bool, float)):
            return str(self.value)
        return None

    def to_int(self) -> Optional[int]:
        """Returns the value if it is an int, None otherwise"""
        if isinstance(self.value, int):
            return self.value
        return None

    def to_float(self) -> Optional[float]:
        """Returns the value if it is a float, None otherwise"""
        if isinstance(self.value, float):
            return self.value
        return None

    def to_bool(self) -> Optional[bool]:
        """Returns the value if it is a bool, None otherwise"""
        if isinstance(self.value, bool):
            return self.value
        return None

    def to_list(self) -> Optional[List[Any]]:
        """Returns the value if it is an list, None otherwise"""
        if isinstance(self.value, list):
            return self.value
        return None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        """Returns the value if it is a dict, None otherwise"""
        if isinstance(self.value, dict):
            return self.value
        return None

    def iter_list(self) -> "Iterator[SafeJSON]":
        """Iterate through self if it is a list
        else yields nothing"""
        if isinstance(self.value, list):
            for x in self.value:
                yield SafeJSON(x)

    def iter_dict(self) -> "Iterator[Tuple[str, SafeJSON]]":
        """Iterate through self if it is a list
        else yields nothing"""
        if isinstance(self.value, dict):
            for key, val in self.value.items():
                yield key, SafeJSON(val)
