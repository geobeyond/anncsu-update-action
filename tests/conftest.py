import sys
import types
import contextlib
import shutil
import tempfile
from pathlib import Path

import pytest

"""Pytest fixtures for tests."""
# Make the package source importable from tests
sys.path.insert(0, "src")

import functions as _functions  # noqa: E402


@pytest.fixture
def fake_core(monkeypatch, tmp_path):
    """Set up fake `actions` package and minimal `anncsu` modules.

    Returns the `core` object so tests can inspect logged messages.
    """
    # Patch functions.check_output to avoid running external commands
    monkeypatch.setattr(_functions, "check_output", lambda *a, **k: "")

    # Fake `actions` package
    actions = types.ModuleType("actions")
    actions.context = types.SimpleNamespace(os="dummy", repo="x")

    class DummyCore:
        def __init__(self):
            self.messages = []

        def get_version(self):
            return "0.0-test"

        def info(self, msg):
            self.messages.append(("info", msg))
            print(f"INFO: {msg}")

        def debug(self, msg):
            self.messages.append(("debug", msg))
            print(f"DEBUG: {msg}")

        def warn(self, msg):
            self.messages.append(("warn", msg))
            print(f"WARN: {msg}")

        def error(self, msg):
            self.messages.append(("error", msg))
            print(f"ERROR: {msg}")

        def get_input(self, name, required=False):
            if name == "geodiff_report":
                return "a json to simulate geodiff report to be patched before test run"
            if name == "token":
                return "fake-token"
            return ""

        def set_failed(self, msg):
            raise RuntimeError(msg)

        def group(self, name):
            return contextlib.nullcontext()

    actions.core = DummyCore()

    # Install the fake actions module
    monkeypatch.setitem(sys.modules, "actions", actions)

    # Create minimal fake `anncsu` package and submodules used by main
    anncsu = types.ModuleType("anncsu")
    pa = types.ModuleType("anncsu.pa")

    class AnncsuConsultazione:
        def __init__(self, security=None):
            self.security = security

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    pa.AnncsuConsultazione = AnncsuConsultazione
    monkeypatch.setitem(sys.modules, "anncsu", anncsu)
    monkeypatch.setitem(sys.modules, "anncsu.pa", pa)

    # anncsu.common.config
    common = types.ModuleType("anncsu.common")
    common_config = types.ModuleType("anncsu.common.config")

    class ClientAssertionSettings:
        def to_config(self, api_type=None):
            return types.SimpleNamespace(audience="https://token.endpoint")

    class APIType:
        ACCESSI = "accessi"

    common_config.ClientAssertionSettings = ClientAssertionSettings
    common_config.APIType = APIType
    monkeypatch.setitem(sys.modules, "anncsu.common", common)
    monkeypatch.setitem(sys.modules, "anncsu.common.config", common_config)

    # anncsu.common functions
    def create_client_assertion(config):
        return "client_assertion"

    class PDNDAuthManager:
        def __init__(self, **kwargs):
            pass

        def get_access_token(self):
            return "access-token-from-manager"

    common.create_client_assertion = create_client_assertion
    common.PDNDAuthManager = PDNDAuthManager
    monkeypatch.setitem(sys.modules, "anncsu.common", common)

    # anncsu.common.session
    common_session = types.ModuleType("anncsu.common.session")

    def get_config_dir():
        return tmp_path

    common_session.get_config_dir = get_config_dir
    monkeypatch.setitem(sys.modules, "anncsu.common.session", common_session)

    # anncsu.coordinate.models.Security
    coord = types.ModuleType("anncsu.coordinate")
    coord_models = types.ModuleType("anncsu.coordinate.models")

    class Security:
        def __init__(self, bearer=None):
            self.bearer = bearer

    coord_models.Security = Security
    monkeypatch.setitem(sys.modules, "anncsu.coordinate", coord)
    monkeypatch.setitem(sys.modules, "anncsu.coordinate.models", coord_models)

    return actions.core


"""Pytest configuration and fixtures for geodiff tests."""


# reusing subset of conftest from geodiff-action codebase
@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    # Cleanup
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def geodiff_delete_json():
    import json

    return json.dumps(
        {
            "geodiff": [
                {
                    "table": "simple",
                    "type": "delete",
                    "changes": [
                        {"column": 0, "old": 2},
                        {"column": 1, "old": "R1AAAeYQAAABAQAAAPBDGq/kSde/+HS2Feb94T8="},
                        {"column": 2, "old": "feature2"},
                        {"column": 3, "old": 2},
                    ],
                }
            ]
        }
    )


@pytest.fixture
def geodiff_update_json():
    import json

    return json.dumps(
        {
            "geodiff": [
                {
                    "table": "simple",
                    "type": "update",
                    "changes": [
                        {"column": 0, "old": 2},
                        {
                            "column": 1,
                            "old": "R1AAAeYQAAABAQAAAPBDGq/kSde/+HS2Feb94T8=",
                            "new": "R1AAAeYQAAABAQAAAMp+uos0te2/hISLbYZyzj8=",
                        },
                        {"column": 3, "old": 2, "new": 9999},
                    ],
                }
            ]
        }
    )


@pytest.fixture
def geodiff_insert_json():
    import json

    return json.dumps(
        {
            "geodiff": [
                {
                    "table": "simple",
                    "type": "insert",
                    "changes": [
                        {"column": 0, "new": 4},
                        {"column": 1, "new": "R1AAAeYQAAABAQAAAFyu1BOp6um/PoMqH8N01j8="},
                        {"column": 2, "new": "my new point A"},
                        {"column": 3, "new": 1},
                    ],
                }
            ]
        }
    )
