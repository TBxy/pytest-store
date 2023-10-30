from __future__ import annotations
import contextlib
import io
from pathlib import Path
from xlsxwriter import Workbook
import sqlite3
from typing import Literal, Optional, Union

import numpy as np

import polars as pl
from icecream import ic

with contextlib.suppress(ModuleNotFoundError):
    from rich import print


from pytest_store.types import STORE_TYPES

from pytest_store.stores._store_base import StoreBase, SaveSettings, SaveExtras


class PolarsDF(StoreBase):
    def __init__(self):
        super().__init__()
        self._data: pl.DataFrame = pl.DataFrame({"RUN": [0]})
        self._idx = 0
        self.set_index(0)

    def set_index(self, idx: int):
        self._idx = idx
        if not self._data.filter(pl.col("RUN") == idx).shape[0]:
            # print(f"index {idx} is missing, add it")
            # self._data = pl.concat([self._data, pl.DataFrame({"index": [idx]})])
            new_df = self._data.clear(1)
            new_df[0, "RUN"] = idx
            self._data.extend(new_df)
            # if len(self._data.iloc[0].values):
            #    self._data.loc[idx] = self._data.loc[0]
            #    self._data.loc[idx, :] = None
            # else:
            #    self._data = pl.concat([self._data, pl.DataFrame({}, index=[idx])])

    def set(self, name: str, value: STORE_TYPES):
        otherwise = pl.col(name) if name in self._data.columns else None
        if isinstance(value, str):
            value = pl.lit(value)
        _updated = self._data.select(pl.when(pl.col("RUN") == self._idx).then(value).otherwise(otherwise).alias(name))
        self._data = self._data.with_columns(_updated)
        return value

    def get(
        self, name: Optional[str] = None, default: STORE_TYPES = None
    ) -> Union[dict[str, STORE_TYPES], STORE_TYPES]:
        if name is None:
            return self._data.filter(pl.col("RUN") == self._idx)
            # return self._data.loc[self._idx]
        # return self._data[int(self._idx), name]
        try:
            value = self._data.filter(pl.col("RUN") == self._idx)[name].item()
        except pl.exceptions.ColumnNotFoundError:
            return default
        if value is None:
            value = default
        if isinstance(value, pl.Series):
            value = value.to_list()
        return value

    def to_string(self, max_lines=30, max_width=0):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            # with pl.option_context("display.max_rows", max_lines):
            print(self._data)
        return f.getvalue()

    def save(self, __save_settings: Union[None, SaveSettings] = None, __extras: Union[None, SaveExtras] = None):
        """See https://pandas.pydata.org/docs/reference/io.html"""
        settings = self._save_settings_list if __save_settings is None else [__save_settings]
        extras = __extras if __extras else SaveExtras()
        extras.settings = settings
        for cfg in settings:
            if cfg.format == "json":
                cfg.default_options({"row_oriented": True, "pretty": True})
            elif cfg.format in ["xls", "xlsx"]:
                cfg.format = "excel"
                cfg.default_options(
                    {
                        "table_name": cfg.name,
                        "worksheet": cfg.name,
                        "freeze_panes": (1, 0),
                        "header_format": {"rotation": 60},
                    }
                )
            func = f"write_{cfg.format}"
            if cfg.format in ["sqlite", "sql"]:
                uri = f"sqlite:///{cfg.path}"
                cfg.default_options({"table_name": cfg.name, "connection": uri, "if_exists": "replace"})
                self._data.write_database(**cfg.options)
            elif cfg.format == "excel":
                # wb = extras.get_extras("excel").get("workbook", Workbook(cfg.path))
                # ic(wb)
                # _read = pl.read_excel(cfg.path)
                # ic(_read)
                # if isinstance(_read, dict):
                #    for sheet, df in _read.items():
                #        df.write_excel(workbook=wb, table_name=sheet, worksheet=sheet)
                # else:
                #    _read.write_excel(workbook=wb)
                extras.set_extras("excel", {"workbook": self._data.write_excel(workbook=cfg.path, **cfg.options)})
            elif hasattr(self._data, func):
                getattr(self._data, func)(cfg.path, **cfg.options)
            else:
                msg = f"Format '{cfg.format}' not supportd by polars, see 'https://pola-rs.github.io/polars/py-polars/html/reference/io.html'"
                raise UserWarning(msg)
        return extras

    # def _save_sqlite(self, path: Union[str, Path], format: str, **options):
    #    cnx = sqlite3.connect(path)
    #    self._data.to_sql(name="store", con=cnx, **options)


if __name__ == "__main__":
    ic()
    store = PolarsDF()

    store.set_index(1)
    store.set("hi", "name")
    store.set("hi", "Hoi")
    store.set("cpu", [3.0, 2.0])
    ic(store.get("cpu"))
    store.set_index(2)
    store.set("hi", 3)
    ic(store.get("cpu", 99))
    store.set("hi", 3)
    store.set("new", 3)
    store.set_index(0)
    store.set("new", 1)
    # store.set("cpu", 2)
    # TODO implement list
    # store.set("list", [1, 2])
    # store.append("list", [23, 23])
    # store.set("cpu", 2)
    extras = store.save(SaveSettings(Path("out.xlsx"), "data_first", "xls", {}))
    store.set_index(3)
    store.set("additional", 1)
    ic(store.get("additional"))
    store.save(SaveSettings(Path("out.xlsx"), "data_second", "xls", {}), extras)
    # extras.get_extras("excel").get("workbook").close()
    print(store)
