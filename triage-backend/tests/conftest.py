"""Pytest helpers for running async tests without external plugins."""

from __future__ import annotations

import asyncio
import inspect
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "asyncio: run test in an event loop")


def pytest_pyfunc_call(pyfuncitem) -> bool | None:
    test_function = pyfuncitem.obj
    if not inspect.iscoroutinefunction(test_function):
        return None

    kwargs = {
        key: value
        for key, value in pyfuncitem.funcargs.items()
        if key in pyfuncitem._fixtureinfo.argnames
    }
    asyncio.run(test_function(**kwargs))
    return True
