from __future__ import annotations

import contextlib
import io
from pathlib import Path
from typing import Optional, Union
import msgspec

from pytest_store.types import STORE_TYPES
from pytest_store.stores._store_base import StoreBase, SaveSettings, SaveExtras


class ListDict(StoreBase):
    def __init__(self):
        super().__init__()
        self._data = []
        self._idx = None
        self.set_index(0)

    def set_index(self, idx: int):
        self._idx = idx
        if idx >= len(self._data):
            self._data.append({})
            self.set_index(idx)

    def set(self, name: str, value: STORE_TYPES):
        if self._idx is not None:
            self._data[self._idx][name] = value
            return value
        return None

    def get(
        self, name: Optional[str] = None, default: STORE_TYPES = None
    ) -> Union[dict[str, STORE_TYPES], STORE_TYPES]:
        if name is None:
            if self._idx is not None:
                return self._data[self._idx]
            else:
                return {}
        if self._idx is not None:
            val = self._data[self._idx].get(name, default)
        else:
            val = None
        return val

    def save(self, __save_settings: Union[None, SaveSettings] = None, __extras: Union[None, SaveExtras] = None):
        """See https://jcristharif.com/msgspec/usage.html"""
        settings = self._save_settings_list if __save_settings is None else [__save_settings]
        extras = __extras if __extras else SaveExtras()
        extras.settings = settings
        for cfg in settings:
            if cfg.format == "yml":
                cfg.format = "yaml"
            if hasattr(msgspec, cfg.format) and hasattr(getattr(msgspec, cfg.format), "encode"):
                enc_cmd = getattr(getattr(msgspec, cfg.format), "encode")
                stream = enc_cmd(self._data)
                with open(cfg.path, "wb") as file:
                    file.write(stream)
        return extras

    def to_string(self, max_lines=40, max_width=0):
        values = msgspec.yaml.encode(self._data).decode("utf-8")
        out_lines = values.split("\n")
        if len(out_lines) > max_lines:
            idx = int(max_lines / 2)
            out_lines = out_lines[0:idx] + ["\n" + " " * 8 + "..." + "\n"] + out_lines[-idx:]
        return "\n".join(out_lines)


if __name__ == "__main__":
    with contextlib.suppress(ModuleNotFoundError):
        from rich import print
    from icecream import ic
    store = ListDict()

    store.set_index(1)
    store.set("hi", 1)
    store.set("cpu", 3)
    ic(store.get("cpu"))
    store.set_index(2)
    ic(store.get("cpu", 99))
    store.set("hi", 3)
    store.set("new", 3)
    store.set_index(0)
    store.set("new", 1)
    # store.set("cpu", 2)
    store.set("list", [1, 2])
    store.append("list", [23, 23])
    # store.set("cpu", 2)
    print(store.data)
