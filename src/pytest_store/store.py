from contextlib import redirect_stdout
import io
from pathlib import Path
from re import S
from typing import Any, Optional, Union

import pandas as pd
import pytest

from .types import STORE_TYPES
from .stores import PandasDF
from .stores._store_base import StoreBase


class Store:
    def __init__(self, store: Optional[StoreBase] = None):
        self._store: Optional[StoreBase] = store
        self._item: Union[None, pytest.Item] = None
        self.save_path = None

    def set_store(self, store: Optional[StoreBase]):
        self._store = store

    @property
    def item(self) -> Union[pytest.Item, None]:
        return self._item

    @item.setter
    def item(self, item: pytest.Item):
        self._item = item

    @property
    def data(self) -> STORE_TYPES:
        if self._store is not None:
            return self._store.data
        return None

    def set_run(self, run: int):
        if self._store is not None:
            self._store.set_index(run)

    def set(self, name: str, value: STORE_TYPES):
        if self._store is not None:
            return self._store.set(name=name, value=value)
        return None

    def append(self, name: str, value: STORE_TYPES):
        if self._store is not None:
            return self._store.append(name=name, value=value)
        return None

    def get(
        self, name: Optional[str] = None, default: STORE_TYPES = None
    ) -> Union[dict[str, STORE_TYPES], STORE_TYPES]:
        if self._store is not None:
            return self._store.get(name=name, default=default)
        return None

    def _prepare_existing_file(self, path: Path, force=True):
        def get_new_name(name, number: int = 1, max=10):
            new_name = f"{name}{number}"
            if Path(new_name).exists() and number < max:
                new_name = get_new_name(name, number + 1, max=max)
            return new_name

        if path.exists:
            if force:
                path.unlink(missing_ok=True)
                return
            path.rename(get_new_name(f"{path.name}.bak"))

    def save(self, path: Union[str, Path], format: str, force=True, **options):
        if isinstance(path, str):
            path = Path(path)
        self._prepare_existing_file(path, force=force)
        if self._store is not None:
            if hasattr(self._store, "save"):
                self._store.save(path, format, **options)
                self.save_path = str(path)
            else:
                msg = f"Save not supported for {self._store}"
                raise UserWarning(msg)
        return Path(path)

    def to_string(self, max_lines: int = 40, max_width: int = 120):
        if self._store is not None and hasattr(self._store, "to_string"):
            return self._store.to_string(max_lines=max_lines, max_width=max_width)
        else:
            f = io.StringIO()
            with redirect_stdout(f):
                print(self.data)
            out_lines = f.getvalue().split("\n")
            if len(out_lines) > max_lines:
                out_lines = out_lines[: max_lines / 2] + out_lines[-max_lines / 2 :]
            return "\n".join(out_lines)


store = Store()
