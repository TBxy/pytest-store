# Python program showing
# abstract base class work
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

from pytest_store.types import STORE_TYPES


class StoreBase(ABC):
    def __init__(self):
        self._data = []
        self._idx = None
        self.set_index(0)

    @property
    def data(self):
        return self._data

    @abstractmethod
    def set_index(self, idx: int) -> None:
        pass

    @abstractmethod
    def set(self, name: str, value: STORE_TYPES) -> STORE_TYPES:
        pass

    def get(
        self, name: Optional[str] = None, default: STORE_TYPES = None
    ) -> Union[dict[str, STORE_TYPES], STORE_TYPES]:
        pass

    def append(self, name: str, value: STORE_TYPES) -> list:
        current_val = self.get(name, [])
        if not isinstance(value, list):
            value = [value]
        if not isinstance(current_val, list):
            current_val = [current_val]
        new_val = current_val + value
        self.set(name, new_val)
        return new_val

    @abstractmethod
    def save(self, path: Union[str, Path], format: str, **options) -> Path:
        pass

    @abstractmethod
    def to_string(self, max_lines=40, max_width=0) -> str:
        pass
