from __future__ import annotations
from typing import Callable, Optional
from ._store_base import StoreBase

Stores: dict[str, Optional[Callable[[], StoreBase]]] = {}
try:
    import polars as pl
    from .polars_df import PolarsDF

    Stores["polars"] = PolarsDF
    Stores["pl"] = PolarsDF
    Stores["default"] = PolarsDF
except ModuleNotFoundError:
    pass


try:
    import pandas as pd
    from .pandas_df import PandasDF

    Stores["pandas"] = PandasDF
    Stores["pd"] = PandasDF
    if "default" not in Stores:
        Stores["default"] = PandasDF
except ModuleNotFoundError:
    pass

from .list_dict import ListDict

Stores["list-dict"] = ListDict
if "default" not in Stores:
    Stores["default"] = ListDict
Stores["none"] = None
