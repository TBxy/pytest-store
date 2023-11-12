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

all_pass_key = pytest.StashKey[bool]()
# item stash keys
store_testname_key = "store_testname"
store_run_key = "store_run"


def pytest_addoption(parser):
    group = parser.getgroup("store")
    group.addoption(
        "--store-type",
        action="store",
        default="default",
        help="Set store type (default: installed extra).",
        choices=[n for n in Stores],
    )
    group.addoption(
        "--store-save", action="store", help="Save file to path, format depends on the ending unless specified."
    )
    group.addoption("--store-save-format", action="store", help="Save format.")
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
    if not (store_obj_str in (None, notset, "", "none") or store_obj_str in Stores):
        raise pytest.UsageError(f"Store type {store_obj_str} does not exist, use {', '.join(Stores.keys())}.")
    if isinstance(store_obj_str, str):
        store_obj_str = store_obj_str.replace("_", "-").lower()
        if store_obj_str in Stores:
            obj = Stores.get(store_obj_str, None)
            if obj is not None:
                store.set_store(obj())


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


def pytest_configure(config):
    set_store_obj(config)
    set_save_to_file(config)


@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter: TerminalReporter, exitstatus, config: pytest.Config):
    # reports = terminalreporter.getreports("")
    # content = os.linesep.join(text for report in reports for secname, text in report.sections)
    if store.__stores__ is not None:
        terminalreporter.ensure_newline()
        terminalreporter.section("stored values summary", sep="=", blue=True, bold=True)
        terminalreporter.write(store.to_string())
        if store.store is not None and store.store._save_settings_list:
            terminalreporter.write("\nSaved to '")
            terminalreporter.write(
                ", ".join([str(s.path) for s in store.store._save_settings_list]), bold=True, green=True
            )
            terminalreporter.write("'\n")


def _use_pytest_repeat(item, count):
    pat = r"(\d+)-\d+\]"
    m = re.search(pat, item.name)
    if item.stash.get(store_run_key, None) is None:
        if m and m.group(1):
            idx = int(m.group(1)) - 1
            item.stash[store_run_key] = int(idx)
    if item.stash.get(store_testname_key, None) is None:
        if m:
            item.stash[store_testname_key] = (
                item.name.replace(f"[{m.group(0)}", "").replace(f"-{m.group(0)}", "]").replace("test_", "")
            )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item: pytest.Item, nextitem: pytest.Item):
    if store.get_index() != item.stash.get(store_run_key, 0):
        store.set_index(item.stash.get(store_run_key, 0))
    if store.get("PASS", default=None, prefix="") is None:
        if (
            item.config.getoption("repeat_scope", None) == "session"
            or item.config.getoption("rerun_time", None)
            or item.config.getoption("rerun_iter", None)
        ):
            store.set("PASS", bool(item.session.stash.get(all_pass_key, True)), prefix="")
            item.session.stash[all_pass_key] = True
    store.item = item
    yield


def pytest_collection_modifyitems(session: pytest.Session, config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # support for pytest-rerun
        # rerun_for = config.getoption("rerun_for", None)
        # if rerun_for is not None:
        #    _use_pytest_rerun(item, rerun_for)
        # support for pytest-repeat
        if item.stash.get(store_testname_key, None) is None:
            count = config.getoption("count", 0)
            if count is not None and count > 1:
                _use_pytest_repeat(item, count)
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if item.stash.get(store_testname_key, None) is None:
            item.stash[store_testname_key] = item.name.replace("test_", "")
        if item.stash.get(store_run_key, None) is None:
            item.stash[store_run_key] = 0
        item.store_testname = item.stash[store_testname_key]


def pytest_runtest_logreport(report: pytest.TestReport):
    item = store.item
    if report.outcome == "skipped" or getattr(item, "_skipped", False):
        setattr(item, "_skipped", True)
        return
    name = "pass"
    if report.when in ("setup", "teardown"):
        name = f"{name}_{report.when}"
    if item is not None:
        if not report.passed:
            item.session.stash[all_pass_key] = False
        store.set(name, report.passed)
        # store.set(f"outcome_{report.when}", report.outcome)


def pytest_sessionfinish(session: pytest.Session, exitstatus: Union[int, pytest.ExitCode]) -> None:
    if session.config.getoption("repeat_scope", None) == "session" or session.config.getoption("rerun_for", None):
        store.set("PASS", bool(session.stash.get(all_pass_key, True)), prefix="")
        session.stash[all_pass_key] = True
    store.save()
    # store_to_file(session.config)


# def pytest_runtest_teardown(item: pytest.Item) -> None:  # noqa: ARG001
#    store.item = None
