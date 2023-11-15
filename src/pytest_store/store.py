from contextlib import redirect_stdout
import io
from pathlib import Path
from re import S
from typing import Any, Optional, Union
import msgspec

import pytest

from icecream import ic
from .types import STORE_TYPES
from .stores._store_base import StoreBase, SaveSettings


class Store:
    def __init__(
        self,
        store: Optional[StoreBase] = None,
        default_name=None,
        default_prefix: str = "{item._store_testname}",  # use either item or testname
    ):
        self.__stores__: dict[str, StoreBase] = {}
        self._default_active_store = "default"
        if default_name is not None:
            self._default_active_store = default_name
        self._active_store = self._default_active_store
        if store is not None:
            self.set_store(store)
        self._default_prefix = default_prefix
        self._item: Union[None, pytest.Item] = None
        self._save_to = []

    def set_store(self, store: Optional[StoreBase], name=None):
        """Set store, optionally with different name. If it already exists it is overwritten. If set to 'None' the store is deleted."""
        if name is None:
            name = self._default_active_store
        if store is None and name in self._stores:
            del self._stores[name]
        if store is not None:
            self._stores[name] = store

    def set_active(self, name="default"):
        self._active_store = name

    def add_store(self, name: str, _from: Optional[str] = None):
        """Add a new store based on 'from', per default use the default one."""
        if _from is None:
            _from = self._default_active_store
        if _from in self._stores:
            self.set_store(type(self._stores[_from])(), name=name)

    @property
    def item(self) -> Union[pytest.Item, None]:
        return self._item

    @item.setter
    def item(self, item: pytest.Item):
        self._item = item

    @property
    def store(self) -> Optional[StoreBase]:
        return self._stores.get(self._active_store, None)

    @property
    def _stores(self) -> dict[str, StoreBase]:
        return self.__stores__

    @property
    def data(self) -> STORE_TYPES:
        if self.store is not None:
            return self.store.data
        return None

    def set_index(self, run: int):
        if self.store is not None:
            self.store.set_index(run)

    def get_index(self) -> int:
        if self.store is not None:
            return self.store._idx
        else:
            return 0

    def set(self, name: str, value: STORE_TYPES, prefix: str = "default"):
        if self.store is not None:
            name = self._get_name_with_prefix(name, prefix)
            return self.store.set(name=name, value=value)
        return None

    def append(self, name: str, value: STORE_TYPES, prefix: str = "default"):
        if self.store is not None:
            name = self._get_name_with_prefix(name, prefix)
            return self.store.append(name=name, value=value)
        return None

    def get(
        self, name: Optional[str] = None, default: STORE_TYPES = None, prefix: str = "default"
    ) -> Union[dict[str, STORE_TYPES], STORE_TYPES]:
        if self.store is not None:
            name = self._get_name_with_prefix(name, prefix)
            return self.store.get(name=name, default=default)
        return None

    def save_to(
        self,
        _path_or_obj: Union[str, Path, dict, SaveSettings],
        format: Optional[str] = None,
        name: Optional[str] = None,
        options: dict[str, Any] = {},
        force: bool = False,
        all_stores: bool = True,
    ):
        obj = self._save_to_obj(_path_or_obj, format=format, name=name, options=options)
        if all_stores:
            for store_name, store in self.__stores__.items():
                if name is None:
                    obj.name = store_name
                # if store_name is not self._default_active_store:
                #    obj.path = obj.path.with_suffix(f"-{name}.{obj.path.suffix}")
                store.save_to(obj)
        elif self.store is not None:
            self.store.save_to(obj)
        self._prepare_existing_file(obj.path, force=force)

    def save(
        self,
        _path_or_obj: Union[None, str, Path] = None,
        format: Optional[str] = None,
        name: Optional[str] = None,
        force: bool = False,
        options: dict[str, Any] = {},
    ):
        obj = None
        if _path_or_obj is not None:
            obj = self._save_to_obj(_path_or_obj, format=format, name=name, options=options)
            self._prepare_existing_file(obj.path, force=force)
        if self.store is not None:
            self.store.save(obj)  # path, format, **options)

    def to_string(self, max_lines: int = 40, max_width: int = 120):
        if self.store is not None and hasattr(self.store, "to_string"):
            return self.store.to_string(max_lines=max_lines, max_width=max_width)
        else:
            f = io.StringIO()
            with redirect_stdout(f):
                print(self.data)
            out_lines = f.getvalue().split("\n")
            if len(out_lines) > max_lines:
                out_lines = out_lines[: max_lines / 2] + out_lines[-max_lines / 2 :]
            return "\n".join(out_lines)

    def _get_name_with_prefix(self, name, prefix):
        if prefix == "default":
            prefix = self._default_prefix
            if self.item is None:
                prefix = "PRE"
        if prefix:
            name = f"{prefix.format(item=self.item)}.{name}"
        return name

    def _save_to_obj(
        self,
        _path_or_obj: Union[str, Path, dict, SaveSettings],
        format: Optional[str] = None,
        name: Optional[str] = None,
        options: dict[str, Any] = {},
    ) -> SaveSettings:
        obj = None
        if name is None:
            name = self._active_store
        if isinstance(_path_or_obj, SaveSettings):
            obj = _path_or_obj
        elif isinstance(_path_or_obj, dict):
            obj = SaveSettings(**_path_or_obj)
        elif isinstance(_path_or_obj, str):
            _path_or_obj = Path(_path_or_obj)
        if isinstance(_path_or_obj, Path):
            if not format:
                format = _path_or_obj.suffix[1:]
            # ic(format, _path_or_obj, _path_or_obj.suffix)
            obj = SaveSettings(path=_path_or_obj, name=name, format=format, options=options)
        if obj is None:
            raise UserWarning(f"Could not create 'SaveSettings' object with type {type(_path_or_obj)}.")
        return obj

    def _prepare_existing_file(self, path: Path, force=True):
        def get_new_name(name, number: int = 1, max=10):
            new_name = f"{name}{number}"
            if Path(new_name).exists() and number < max:
                new_name = get_new_name(name, number + 1, max=max)
            return new_name

        if path.exists():
            if force:
                path.unlink(missing_ok=True)
                return
            # ic(path)
            path.rename(get_new_name(f"{path.name}.bak"))


store = Store()
