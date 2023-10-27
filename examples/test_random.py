import psutil
import pytest
from typing import Literal
from rich import print
import random

from pytest_store import store


def test_randint():
    numbers = [random.randint(5, 10) for _i in range(1, random.randint(2, 4))]
    store.set("randint", numbers)
    assert len(numbers) < 3


def test_append_randint():
    numbers = [random.randint(0, 5) for _i in range(1, random.randint(1, 3))]
    store.append("randint", numbers)
    all_numbers: list = store.get("randint", [])
    assert len(all_numbers) < 5
