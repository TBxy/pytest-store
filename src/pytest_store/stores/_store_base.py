# Python program showing
# abstract base class work
from abc import ABC, abstractmethod
import contextlib
import io
from pathlib import Path
from typing import Any, Optional, Union

import msgspec

from pytest_store.types import STORE_TYPES, STORE_TYPES_SINGLE


class SaveSettings(msgspec.Struct):
    """Settings used for saving data to ..."""

    path: Path
    name: str
    format: str
    options: dict[str, Any] = {}

    def default_options(self, options: dict[str, Any] = {}):
        options.update(self.options)  # type: ignore
        self.options = options


class SaveExtras(msgspec.Struct):
    """Returned values from the save object"""

    settings: list[SaveSettings] = []
    extras_by_format: dict[str, Any] = {}

    def get_extras(self, format):
        return self.extras_by_format.get(format, {})

    def set_extras(self, format, values: Any):
        self.extras_by_format[format] = values


class StoreBase(ABC):
    def __init__(self):
        self._data = []
        self._idx = None
        self._save_settings_list: list[SaveSettings] = []

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

    def append(self, name: str, value: Union[STORE_TYPES_SINGLE, list[STORE_TYPES_SINGLE]]) -> list[STORE_TYPES_SINGLE]:
        current_val = self.get(name, [])
        if not isinstance(value, list):
            value = [value]
        if not isinstance(current_val, list):
            current_val = [current_val]
        new_val: list[STORE_TYPES_SINGLE] = current_val + value
        self.set(name, new_val)
        return new_val

    def save_to(self, __obj: SaveSettings):
        self._save_settings_list.append(__obj)

    @abstractmethod
    def save(self, __save_settings: Union[None, SaveSettings] = None, _previous_return: Any = None) -> SaveExtras:
        # for save_settings in self._save_settings_list:
        #    save(save_settings.path)
        return self._save_settings_list

    def to_string(self, max_lines=40, max_width=0) -> str:
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            print(self._data)
        return f.getvalue()

    def __str__(self):
        return self.to_string()
