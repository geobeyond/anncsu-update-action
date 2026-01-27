"""Tests for src/main.py"""

import sys


def test_main_imports_and_runs_geodiff_insert(fake_core, geodiff_insert_json):
    """Import `main` and verify it completes using the `fake_core` fixture in conftest.py."""
    import importlib

    # modify the input to simulate an insert action
    fake_core.get_input = lambda name, required=False: (
        geodiff_insert_json if name == "geodiff_report" else "fake-token"
    )

    if "main" in sys.modules:
        importlib.reload(sys.modules["main"])
    else:
        importlib.import_module("main")

    assert any("Anncsu Update Action completed" in m for _, m in fake_core.messages)


def test_main_imports_and_runs_geodiff_update(fake_core, geodiff_update_json):
    """Import `main` and verify it completes using the `fake_core` fixture in conftest.py."""
    import importlib

    # modify the input to simulate an update action
    fake_core.get_input = lambda name, required=False: (
        geodiff_update_json if name == "geodiff_report" else "fake-token"
    )

    if "main" in sys.modules:
        importlib.reload(sys.modules["main"])
    else:
        importlib.import_module("main")

    assert any("Anncsu Update Action completed" in m for _, m in fake_core.messages)


def test_main_imports_and_runs_geodiff_delete(fake_core, geodiff_delete_json):
    """Import `main` and verify it completes using the `fake_core` fixture in conftest.py."""
    import importlib

    # modify the input to simulate a delete action
    fake_core.get_input = lambda name, required=False: (
        geodiff_delete_json if name == "geodiff_report" else "fake-token"
    )

    if "main" in sys.modules:
        importlib.reload(sys.modules["main"])
    else:
        importlib.import_module("main")

    assert any("Anncsu Update Action completed" in m for _, m in fake_core.messages)
