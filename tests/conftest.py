import sys
import types
from types import SimpleNamespace
from contextlib import contextmanager
from pathlib import Path

import pytest

"""Pytest fixtures for tests."""
# Make the package source importable from tests
sys.path.insert(0, "src")


@pytest.fixture
def mock_env_file(tmp_path: Path) -> Path:
    """Create a mock .env file with test credentials."""
    env_content = """
ANNCSU_UPDATE_CODICE_COMUNE=I501
"""
    env_file = tmp_path / ".env"
    env_file.write_text(env_content.strip())
    return env_file


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


# a read geodiff modification report fixture
@pytest.fixture
def geodiff_real_value_update_json():
    import json

    # NOTE: PK are
    # columns: 0: address_id (AKA PROGRESSIVO_ACCESSO)
    # columns: 2: road_id (AKA PROGRESSIVO_NAZIONALE)
    return json.dumps(
        {
            "geodiff": [
                {
                    "changes": [
                        {"column": 0, "old": 28671617},
                        {"column": 2, "old": 1222582},
                        {"column": 6, "new": "4", "old": "44"},
                    ],
                    "table": "WhereAbouts_fails",
                    "type": "update",
                }
            ]
        }
    )


@pytest.fixture
def geodiff_real_coord_update_json():
    import json

    # NOTE: PK are
    # columns: 0: address_id (AKA PROGRESSIVO_ACCESSO)
    # columns: 2: road_id (AKA PROGRESSIVO_NAZIONALE)
    return json.dumps(
        {
            "geodiff": [
                {
                    "changes": [
                        {"column": 0, "old": 28671616},
                        {
                            "column": 1,
                            "new": "R1AAAQAAAAABAQAAAAAAAICcwitAAAAAwInzREA=",
                            "old": "R1AAAQAAAAABAQAAAObiXKWtwitAXt3+bojzREA=",
                        },
                        {"column": 2, "old": 1222582},
                    ],
                    "table": "WhereAbouts_fails",
                    "type": "update",
                }
            ]
        }
    )


# reusing subset of conftest from geodiff-action codebase
# @pytest.fixture
# def temp_dir():
#     """Create a temporary directory for test files."""
#     tmpdir = tempfile.mkdtemp()
#     yield Path(tmpdir)
#     # Cleanup
#     shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def fake_functions_module():
    mod = types.ModuleType("functions")

    def fake_check_output(*_a, **_kw):
        return ""

    mod.check_output = fake_check_output
    return mod


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


@pytest.fixture
def make_fake_actions_module():
    def _make(geodiff_report_text):
        mod = types.ModuleType("actions")

        class DummyCore:
            def __init__(self):
                self._failed = None

            def get_version(self):
                return "0.1"

            def info(self, *_a, **_kw):
                return None

            def debug(self, *_a, **_kw):
                return None

            def warn(self, *_a, **_kw):
                return None

            def error(self, *_a, **_kw):
                return None

            def set_failed(self, msg):
                self._failed = msg

            def group(self, *_a, **_kw):
                # simple context manager
                @contextmanager
                def _cm():
                    yield None

                return _cm()

            def get_input(self, name, required=False):
                if name == "geodiff_report":
                    return geodiff_report_text
                if name == "token":
                    return "FAKE-TOKEN"
                return ""

        # simple context object with an 'os' attribute (the real code deletes it)
        context = SimpleNamespace(os=object(), repo={"name": "x"})

        core = DummyCore()

        mod.context = context
        mod.core = core
        return mod

    return _make


@pytest.fixture
def make_fake_settings_module():
    def _make():
        mod = types.ModuleType("settings")

        class AnncsuUpdateSettings:
            def __init__(self):
                self.codice_comune = "I501"

            def model_dump_json(self):
                settings = """{
                    "ANNCSU_UPDATE_CODICE_COMUNE": "I501"
                }"""
                return settings.replace("\n", "").replace(" ", "")

        mod.AnncsuUpdateSettings = AnncsuUpdateSettings
        return mod

    return _make


@pytest.fixture
def make_fake_pygeodiff_and_shapely():
    def _make():
        pygeodiff = types.ModuleType("pygeodiff")

        class GeoDiff:
            def create_wkb_from_gpkg_header(self, data):
                return [b"FAKE-WKB"]

        pygeodiff.GeoDiff = GeoDiff

        shapely = types.ModuleType("shapely")
        wkb = types.ModuleType("shapely.wkb")

        class FakeGeometry:
            is_valid = True
            geom_type = "Point"

            def __init__(self, coords):
                self._coords = coords

            @property
            def coords(self):
                return self._coords

        def loads(_bytes):
            return FakeGeometry([(12.34, 56.78)])

        wkb.loads = loads

        class Point:
            def __init__(self, coord):
                self.x, self.y = coord

        shapely.wkb = wkb
        shapely.Point = Point

        return pygeodiff, shapely

    return _make


@pytest.fixture
def DummyCliRunner():
    class DummyCliRunner:
        def invoke(self, app, args):
            return SimpleNamespace(exit_code=0, output="ok")

    return DummyCliRunner
