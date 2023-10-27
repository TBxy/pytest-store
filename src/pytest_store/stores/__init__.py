from __future__ import annotations

Stores = {}
try:
    import pandas as pd
    from .pandas_df import PandasDF

    Stores["pandas"] = PandasDF
    Stores["pd"] = PandasDF
except ModuleNotFoundError:
    pass

from .list_dict import ListDict

Stores["list-dict"] = ListDict
