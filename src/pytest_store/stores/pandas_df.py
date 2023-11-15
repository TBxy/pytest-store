from __future__ import annotations
import contextlib
import io
from pathlib import Path
import sqlite3
from typing import Optional, Union

import numpy as np
import pandas as pd
from icecream import ic

with contextlib.suppress(ModuleNotFoundError):
    from rich import print


from pytest_store.types import STORE_TYPES

from pytest_store.stores._store_base import StoreBase, SaveSettings, SaveExtras


class PandasDF(StoreBase):
    def __init__(self):
        super().__init__()
        self._data = pd.DataFrame(columns=["RUN"], index=[0])
        self._idx = None
        self.set_index(0)

    def set_index(self, idx: int):
        self._idx = idx
        if idx not in self._data.index:
            # print(f"index '{idx}' is missing, add it")
            if len(self._data.iloc[0].values):
                self._data.loc[idx] = self._data.loc[0]
                self._data.loc[idx, :] = None
            else:
                self._data = pd.concat([self._data, pd.DataFrame({}, index=[idx])])
            self._data["RUN"] = self._data.index.copy()

    def set(self, name: str, value: STORE_TYPES):
        if isinstance(value, (dict, list)):
            self._data.at[self._idx, name] = None
        self._data.at[self._idx, name] = value
        return value

    def get(
        self, name: Optional[str] = None, default: STORE_TYPES = None
    ) -> Union[dict[str, STORE_TYPES], STORE_TYPES]:
        if name is None:
            return self._data.loc[self._idx]
        try:
            val = self._data.at[self._idx, name]
        except KeyError:
            return default
        # if val is None or np.isnan(val):
        if not isinstance(val, list) and val is not None and np.isnan(val):
            return default
        return val

    def to_string(self, max_lines=30, max_width=0):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            _idx = self._data.index.copy()
            self._data.index = [""] * len(_idx)
            with pd.option_context("display.max_rows", max_lines):
                print(self._data)
            self._data.index = _idx
        return f.getvalue()

    def save(self, __save_settings: Union[None, SaveSettings] = None, __extras: Union[None, SaveExtras] = None):
        """See https://pandas.pydata.org/docs/reference/io.html"""
        settings = self._save_settings_list if __save_settings is None else [__save_settings]
        extras = __extras if __extras else SaveExtras()
        extras.settings = settings
        for cfg in settings:
            cfg.default_options({"index": False})
            # print(f"Format '{cfg.format}'", settings)
            if cfg.format in ["xls", "xlsx"]:
                cfg.format = "excel"
                cfg.default_options(
                    {
                        "sheet_name": cfg.name,
                        "freeze_panes": (1, 0),
                        "engine_kwargs": {},
                    }
                )
            elif cfg.format == "md":
                cfg.format = "markdown"
            func = f"to_{cfg.format}"
            if cfg.format == "sqlite":
                self._save_sqlite(cfg.path, cfg.format, **cfg.options)
            elif hasattr(self._data, func):
                getattr(self._data, func)(cfg.path, **cfg.options)
            else:
                msg = f"Format '{cfg.format}' not supportd by pandas (file: {cfg.path}), see 'https://pandas.pydata.org/docs/reference/io.html'"
                raise UserWarning(msg)
        return extras

    def _save_sqlite(self, path: Union[str, Path], format: str, **options):
        cnx = sqlite3.connect(path)
        self._data.to_sql(name="store", con=cnx, **options)


if __name__ == "__main__":
    store = PandasDF()

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
