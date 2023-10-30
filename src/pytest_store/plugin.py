# -*- coding: utf-8 -*-

import os
from typing import Callable, Optional, Union
import warnings
from click import UsageError
import pytest

import pathlib
from .store import store
from .stores import Stores
from rich import print
import re
from icecream import ic

from _pytest.config import notset, Notset
from _pytest.terminal import TerminalReporter


def pytest_addoption(parser):
    group = parser.getgroup("store")
    group.addoption("--store-type", action="store", help="Set store type (default: pandas).")
    group.addoption(
        "--store-save", action="store", help="Save file to path, format depends on the ending unless specified."
    )
    group.addoption("--store-save-format", choices=[n for n in Stores], action="store", help="Save format.")
    group.addoption("--store-save-force", action="store_true", help="Overwrite exisintg file")

    parser.addini("store_type", "Set store type")
    parser.addini("store_save", "Save file to path, format depends on the ending unless specified.")
    parser.addini("store_save_format", "Save format.")
    parser.addini("store_save_options", "Additional options for saving")
    parser.addini("store-save-force", help="Overwrite exisintg file")


_OPTION_TYPE = Union[None, int, float, str, Notset]


def get_option_or_ini(
    name: str, config: pytest.Config, default: _OPTION_TYPE = None, format: Callable = str
) -> _OPTION_TYPE:
    option_value: _OPTION_TYPE = default
    if not (config.getoption(name) in (None, notset)):
        option_value = config.getoption(name)
    elif not (config.getini(name) in (None, notset)):
        option_value = config.getini(name)  # type: ignore

    if not (option_value in (None, notset)):
        return format(option_value)
    return option_value


def set_store_obj(config: pytest.Config):
    store_obj_str = get_option_or_ini("store_type", config, default="none")
    store_obj_str = store_obj_str.replace("_", "-").lower()
    if store_obj_str in Stores:
        store.set_store(Stores[store_obj_str]())
    elif not (config.getini("store_type") in (None, notset, "", "none")):
        raise UsageError(f"Store type {store_obj_str} does not exist, use {', '.join(Stores.keys())}.")


def set_save_to_file(config: pytest.Config):
    save_path = get_option_or_ini("store_save", config, default=None)
    save_format = get_option_or_ini("store_save_format", config, default=None)
    save_force = get_option_or_ini("store_save_force", config, default=False, format=bool)
    if not save_path:
        return
    if not (config.getini("store_save_options") in (None, notset, "")):
        # TODO: maybe need to parse to dict
        options: dict = config.getini("store_save_options")  # type: ignore
    else:
        options = {}
    store.save_to(str(save_path), format=save_format, force=bool(save_force), options=options)
    # store.save(save_path, format=str(save_format), force=bool(save_force), **options)


def pytest_configure(config):
    set_store_obj(config)
    set_save_to_file(config)


@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter: TerminalReporter, exitstatus, config: pytest.Config):
    reports = terminalreporter.getreports("")
    # content = os.linesep.join(text for report in reports for secname, text in report.sections)
    if store.__stores__ is not None:
        terminalreporter.ensure_newline()
        terminalreporter.section("stored values summary", sep="=", blue=True, bold=True)
        # print(store.store)
        terminalreporter.write(store.to_string())
        if store.store is not None and store.store._save_settings_list:
            terminalreporter.write("\nSaved to '")
            terminalreporter.write(
                ", ".join([str(s.path) for s in store.store._save_settings_list]), bold=True, green=True
            )
            terminalreporter.write("'\n")
            # terminalreporter.write_sep(sep="-", title="oke")


def _use_pytest_rerun(item, rerun_for):
    if not hasattr(item, "store_run") or getattr(item, "_use_store_run", False):
        item.store_run = getattr(item, "execution_count", 0)
        item._use_store_run = True


def _use_pytest_repeat(item, count):
    if not hasattr(item, "store_run"):
        pat = r"(\d+)-\d+\]"
        m = re.search(pat, item.name)
        if m and m.group(1):
            idx = int(m.group(1)) - 1
            item.store_run = idx
    if not hasattr(item, "store_testname"):
        pat = r"(\d+)-\d+\]"
        m = re.search(pat, item.name)
        if m and m.group(1):
            idx = int(m.group(1)) - 1
            store.set_index(idx)
            item.store_run = idx
        item.store_testname = item.name.replace(f"[{m.group(0)}", "").replace(f"-{m.group(0)}", "]")


@pytest.hookimpl(trylast=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    # TODO: need to adapot --count to know which iteration and then make new entry
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # support for pytest-repeat
    count = item.config.getoption("count", 0)
    rerun_for = item.config.getoption("rerun_for", None)
    if rerun_for is not None:
        _use_pytest_rerun(item, rerun_for)
    elif count is not None and count > 1:
        _use_pytest_repeat(item, count)
    # if not hasattr(item, "store_run"):
    #    count = item.config.getoption("count", 0)
    #    pat = None
    #    if count is not None and count > 1:
    #        pat = r"(\d+)-\d+\]"
    #    if pat:
    #        m = re.search(pat, item.name)
    #        if m and m.group(1):
    #            idx = int(m.group(1)) - 1
    #            item.store_run = idx
    # if not hasattr(item, "store_testname"):
    #    count = item.config.getoption("count", 0)
    #    pat = None
    #    if count is not None and count > 1:
    #        pat = r"(\d+)-\d+\]"
    #    if pat:
    #        m = re.search(pat, item.name)
    #        if m and m.group(1):
    #            idx = int(m.group(1)) - 1
    #            store.set_index(idx)
    #            item.store_run = idx
    #        item.store_testname = item.name.replace(f"[{m.group(0)}", "").replace(f"-{m.group(0)}", "]")
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    if not hasattr(item, "store_testname"):
        item.store_testname = item.nodeid
    if not hasattr(item, "store_run"):
        item.store_run = 0
    store.item = item
    store.set_index(item.store_run)


def pytest_runtest_logreport(report: pytest.TestReport):
    if report.when == "teardown":
        item = store.item
        if item is not None:
            store.set(f"{item.store_testname}_pass", report.passed)
            # store.set(f"{item.store_testname}_outcome", report.outcome)


def pytest_sessionfinish(session: pytest.Session, exitstatus: Union[int, pytest.ExitCode]) -> None:
    store.save()
    # store_to_file(session.config)


# def pytest_runtest_teardown(item: pytest.Item) -> None:  # noqa: ARG001
#    store.item = None
