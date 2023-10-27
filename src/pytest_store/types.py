from __future__ import annotations

from typing import Union


STORE_TYPES_SINGLE = Union[None, str, int, float]
STORE_TYPES = Union[None, list[STORE_TYPES_SINGLE], dict[str, STORE_TYPES_SINGLE], str, int, float]
