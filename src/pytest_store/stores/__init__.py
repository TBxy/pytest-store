from __future__ import annotations

Stores = {}
try:
    import pandas as pd
    from .pandas_df import PandasDF

    Stores["pandas"] = PandasDF
    Stores["pd"] = PandasDF
except ModuleNotFoundError:
    pass
try:
    import polars as pl
    from .polars_df import PolarsDF

    Stores["polars"] = PolarsDF
    Stores["pl"] = PolarsDF
except ModuleNotFoundError:
    pass


from .list_dict import ListDict

Stores["list-dict"] = ListDict
