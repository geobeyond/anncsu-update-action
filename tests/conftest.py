"""Pytest fixtures for tests."""

import sys
import json
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from contextlib import contextmanager
from typing import Any

import pytest

# Make the package source importable from tests
sys.path.insert(0, "src")


# ============================================================================
# Mock Classes for Dependency Injection
# ============================================================================


@dataclass
class MockLogger:
    """Mock logger that captures all log messages."""

    messages: list[tuple[str, str]] = field(default_factory=list)
    failed_message: str | None = None
    version: str = "1.0.0-test"

    def get_version(self) -> str:
        return self.version

    def info(self, message: str) -> None:
        self.messages.append(("info", message))

    def debug(self, message: str) -> None:
        self.messages.append(("debug", message))

    def warn(self, message: str) -> None:
        self.messages.append(("warn", message))

    def error(self, message: str) -> None:
        self.messages.append(("error", message))

    def set_failed(self, message: str) -> None:
        self.failed_message = message

    def group(self, name: str) -> Any:
        @contextmanager
        def _cm():
            yield None

        return _cm()

    def get_input(self, name: str, required: bool = False) -> str:
        return ""


@dataclass
class MockSettings:
    """Mock settings object."""

    codice_comune: str = "I501"
    coordinate_distance_threshold: float = 0.001
    geocoded_table: str = "geocoded_civici"

    def model_dump_json(self) -> str:
        return json.dumps(
            {
                "ANNCSU_UPDATE_CODICE_COMUNE": self.codice_comune,
                "coordinate_distance_threshold": self.coordinate_distance_threshold,
            }
        )


@dataclass
class MockCliResult:
    """Mock CLI invocation result."""

    exit_code: int = 0
    output: str = "OK"


@dataclass
class MockCliRunner:
    """Mock CLI runner that captures invocations."""

    invocations: list[tuple[Any, list[str]]] = field(default_factory=list)
    result: MockCliResult = field(default_factory=MockCliResult)
    results_sequence: list[MockCliResult] = field(default_factory=list)
    _call_count: int = 0

    def invoke(self, app: Any, args: list[str]) -> MockCliResult:
        self.invocations.append((app, args))
        if self.results_sequence:
            result = self.results_sequence[self._call_count % len(self.results_sequence)]
            self._call_count += 1
            return result
        return self.result


@dataclass
class MockGeoDiff:
    """Mock GeoDiff for geometry conversion."""

    wkb_result: bytes = b"FAKE-WKB"
    should_raise: bool = False

    def create_wkb_from_gpkg_header(self, data: bytes) -> list[bytes]:
        if self.should_raise:
            raise ValueError("Mock GeoDiff error")
        return [self.wkb_result]


@dataclass
class MockGeometry:
    """Mock shapely geometry object."""

    is_valid: bool = True
    geom_type: str = "Point"
    _coords: list[tuple[float, float]] = field(default_factory=lambda: [(12.34, 56.78)])

    @property
    def coords(self) -> list[tuple[float, float]]:
        return self._coords


@dataclass
class MockPoint:
    """Mock shapely Point class."""

    x: float = 0.0
    y: float = 0.0

    def __init__(self, coord: tuple[float, float]):
        self.x = coord[0]
        self.y = coord[1]


@dataclass
class MockAnncsuRecord:
    """Mock ANNCSU record returned by SDK."""

    coord_x: float | None = 10.0  # Different from mock_wkb_loader (12.34)
    coord_y: float | None = 50.0  # Different from mock_wkb_loader (56.78)
    dug: str = "R1AAAQAAAAABAQAAAAAAAICcwitAAAAAwInzREA="


@dataclass
class MockAnncsuResponse:
    """Mock ANNCSU SDK response."""

    res: str = "OK"
    message: str = ""
    data: list[MockAnncsuRecord] = field(default_factory=lambda: [MockAnncsuRecord()])


@dataclass
class MockPathParam:
    """Mock ANNCSU SDK pathparam."""

    response: MockAnncsuResponse = field(default_factory=MockAnncsuResponse)

    def prognazarea_get_path_param(self, prognaz: str) -> MockAnncsuResponse:
        return self.response


@dataclass
class MockAnncsuConsultazione:
    """Mock ANNCSU SDK consultazione class."""

    pathparam: MockPathParam = field(default_factory=MockPathParam)

    def __init__(self, security: Any = None):
        self.pathparam = MockPathParam()


@dataclass
class MockSecurity:
    """Mock ANNCSU Security class."""

    bearer: str = "test-token"
    validate_expiration: bool = True


# ============================================================================
# Fixtures - Mocks
# ============================================================================


@pytest.fixture
def mock_logger() -> MockLogger:
    """Create a fresh mock logger."""
    return MockLogger()


@pytest.fixture
def mock_settings() -> MockSettings:
    """Create mock settings."""
    return MockSettings()


@pytest.fixture
def mock_cli_runner() -> MockCliRunner:
    """Create a mock CLI runner."""
    return MockCliRunner()


@pytest.fixture
def mock_geodiff() -> MockGeoDiff:
    """Create a mock GeoDiff."""
    return MockGeoDiff()


@pytest.fixture
def mock_wkb_loader():
    """Create a mock WKB loader function."""

    def _loader(data: bytes) -> MockGeometry:
        return MockGeometry()

    return _loader


@pytest.fixture
def mock_point_class():
    """Return the MockPoint class."""
    return MockPoint


@pytest.fixture
def mock_cli_app():
    """Mock CLI app object."""
    return SimpleNamespace(name="mock-anncsu-cli")


@pytest.fixture
def mock_anncsu_security() -> MockSecurity:
    """Create a mock ANNCSU Security object."""
    return MockSecurity()


@pytest.fixture
def mock_anncsu_consultazione() -> MockAnncsuConsultazione:
    """Create a mock ANNCSU Consultazione SDK."""
    return MockAnncsuConsultazione()


# ============================================================================
# Fixtures - Environment
# ============================================================================


@pytest.fixture
def mock_env_file(tmp_path: Path) -> Path:
    """Create a mock .env file with test credentials."""
    env_content = """
ANNCSU_UPDATE_CODICE_COMUNE=I501
"""
    env_file = tmp_path / ".env"
    env_file.write_text(env_content.strip())
    return env_file


# ============================================================================
# Fixtures - Geodiff JSON Data
# ============================================================================


@pytest.fixture
def geodiff_update_json():
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
def geodiff_real_value_update_json():
    """Geodiff update without geometry change (only value change)."""
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
    """Geodiff update with coordinate change."""
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


@pytest.fixture
def geodiff_delete_json():
    return json.dumps(
        {
            "geodiff": [
                {
                    "table": "simple",
                    "type": "delete",
                    "changes": [
                        {"column": 0, "old": 2},
                        {"column": 1, "old": "R1AAAeYQAAABAQAAAPBDGq/kSde/+HS2Feb94T8="},
                        {"column": 2, "old": 202},  # road_id should be integer
                        {"column": 3, "old": "feature2"},  # other field
                    ],
                }
            ]
        }
    )


@pytest.fixture
def geodiff_insert_json():
    return json.dumps(
        {
            "geodiff": [
                {
                    "table": "simple",
                    "type": "insert",
                    "changes": [
                        {"column": 0, "new": 4},
                        {"column": 1, "new": "R1AAAeYQAAABAQAAAFyu1BOp6um/PoMqH8N01j8="},
                        {"column": 2, "new": 401},  # road_id should be integer
                        {"column": 3, "new": "my new point A"},  # other field
                    ],
                }
            ]
        }
    )


@pytest.fixture
def geodiff_multiple_entries_json():
    """Geodiff with multiple entries of different types."""
    return json.dumps(
        {
            "geodiff": [
                {
                    "table": "addresses",
                    "type": "update",
                    "changes": [
                        {"column": 0, "old": 1001},
                        {"column": 1, "new": "R1AAAQAAAAABAQAAAAAAAICcwitAAAAAwInzREA="},
                        {"column": 2, "old": 5001},
                    ],
                },
                {
                    "table": "addresses",
                    "type": "insert",
                    "changes": [
                        {"column": 0, "new": 1002},
                        {"column": 1, "new": "R1AAAeYQAAABAQAAAFyu1BOp6um/PoMqH8N01j8="},
                        {"column": 2, "new": 5002},
                    ],
                },
                {
                    "table": "addresses",
                    "type": "delete",
                    "changes": [
                        {"column": 0, "old": 1003},
                        {"column": 1, "old": "R1AAAeYQAAABAQAAAPBDGq/kSde/+HS2Feb94T8="},
                        {"column": 2, "old": 5003},
                    ],
                },
            ]
        }
    )


@pytest.fixture
def geodiff_empty_json():
    """Empty geodiff file (no entries)."""
    return json.dumps({"geodiff": []})


# ============================================================================
# Fixtures - Geodiff Report Files (for integration tests)
# ============================================================================


@pytest.fixture
def geodiff_update_report_file(tmp_path):
    """Create a geodiff update report file as in test.yaml workflow.

    This mirrors the "Create geodiff fake update report" step in test.yaml.
    """
    report_content = {
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
    report_file = tmp_path / "geodiff_update_report.json"
    report_file.write_text(json.dumps(report_content, indent=2))
    return report_file


@pytest.fixture
def geodiff_delete_report_file(tmp_path):
    """Create a geodiff delete report file.

    This mirrors the delete scenario in test-delete-check-with-geodiff.
    """
    report_content = {
        "geodiff": [
            {
                "table": "test_layer",
                "type": "delete",
                "changes": [
                    {"column": 0, "old": 2},
                    {"column": 1, "old": "R1AAAeYQAAABAQAAAPBDGq/kSde/+HS2Feb94T8="},
                    {"column": 2, "old": 202},  # road_id should be integer
                    {"column": 3, "old": "Point B"},  # other field
                    {"column": 4, "old": 2},
                ],
            },
            {
                "table": "test_layer",
                "type": "delete",
                "changes": [
                    {"column": 0, "old": 4},
                    {"column": 1, "old": "R1AAAeYQAAABAQAAAFyu1BOp6um/PoMqH8N01j8="},
                    {"column": 2, "old": 404},  # road_id should be integer
                    {"column": 3, "old": "Point D"},  # other field
                    {"column": 4, "old": 4},
                ],
            },
        ]
    }
    report_file = tmp_path / "geodiff_delete_report.json"
    report_file.write_text(json.dumps(report_content, indent=2))
    return report_file


@pytest.fixture
def geodiff_insert_report_file(tmp_path):
    """Create a geodiff insert report file.

    This mirrors the insert scenario in test-insert-check-with-geodiff.
    """
    report_content = {
        "geodiff": [
            {
                "table": "test_layer",
                "type": "insert",
                "changes": [
                    {"column": 0, "new": 6},
                    {"column": 1, "new": "R1AAAeYQAAABAQAAAFyu1BOp6um/PoMqH8N01j8="},
                    {"column": 2, "new": 606},  # road_id should be integer
                    {"column": 3, "new": "Inserted Point F"},  # other field
                    {"column": 4, "new": 6},
                ],
            },
            {
                "table": "test_layer",
                "type": "insert",
                "changes": [
                    {"column": 0, "new": 7},
                    {"column": 1, "new": "R1AAAeYQAAABAQAAAPBDGq/kSde/+HS2Feb94T8="},
                    {"column": 2, "new": 707},  # road_id should be integer
                    {"column": 3, "new": "Inserted Point G"},  # other field
                    {"column": 4, "new": 7},
                ],
            },
        ]
    }
    report_file = tmp_path / "geodiff_insert_report.json"
    report_file.write_text(json.dumps(report_content, indent=2))
    return report_file


@pytest.fixture
def geodiff_mixed_report_file(tmp_path):
    """Create a geodiff report with mixed operations (insert, update, delete).

    This tests processing multiple operation types in a single report.
    """
    report_content = {
        "geodiff": [
            {
                "table": "test_layer",
                "type": "update",
                "changes": [
                    {"column": 0, "old": 1},
                    {"column": 1, "new": "R1AAAQAAAAABAQAAAAAAAICcwitAAAAAwInzREA="},
                    {"column": 2, "old": 101},
                ],
            },
            {
                "table": "test_layer",
                "type": "insert",
                "changes": [
                    {"column": 0, "new": 10},
                    {"column": 1, "new": "R1AAAeYQAAABAQAAAFyu1BOp6um/PoMqH8N01j8="},
                    {"column": 2, "new": 1010},
                ],
            },
            {
                "table": "test_layer",
                "type": "delete",
                "changes": [
                    {"column": 0, "old": 5},
                    {"column": 1, "old": "R1AAAeYQAAABAQAAAPBDGq/kSde/+HS2Feb94T8="},
                    {"column": 2, "old": 505},
                ],
            },
        ]
    }
    report_file = tmp_path / "geodiff_mixed_report.json"
    report_file.write_text(json.dumps(report_content, indent=2))
    return report_file


# ============================================================================
# Fixtures - GeoPackage files (for geodiff comparison tests)
# ============================================================================


@pytest.fixture
def base_geopackage(tmp_path):
    """Create a base GeoPackage file with test data.

    This mirrors the GeoPackage creation in the workflow steps.
    """
    import sqlite3

    gpkg_path = tmp_path / "base.gpkg"

    conn = sqlite3.connect(gpkg_path)
    cursor = conn.cursor()

    # Create required GeoPackage tables
    cursor.executescript("""
        CREATE TABLE gpkg_spatial_ref_sys (
            srs_name TEXT NOT NULL,
            srs_id INTEGER NOT NULL PRIMARY KEY,
            organization TEXT NOT NULL,
            organization_coordsys_id INTEGER NOT NULL,
            definition TEXT NOT NULL,
            description TEXT
        );

        CREATE TABLE gpkg_contents (
            table_name TEXT NOT NULL PRIMARY KEY,
            data_type TEXT NOT NULL,
            identifier TEXT UNIQUE,
            description TEXT DEFAULT '',
            last_change DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            min_x DOUBLE,
            min_y DOUBLE,
            max_x DOUBLE,
            max_y DOUBLE,
            srs_id INTEGER
        );

        CREATE TABLE gpkg_geometry_columns (
            table_name TEXT NOT NULL,
            column_name TEXT NOT NULL,
            geometry_type_name TEXT NOT NULL,
            srs_id INTEGER NOT NULL,
            z TINYINT NOT NULL,
            m TINYINT NOT NULL,
            CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name)
        );

        INSERT INTO gpkg_spatial_ref_sys VALUES (
            'WGS 84', 4326, 'EPSG', 4326,
            'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]',
            NULL
        );

        CREATE TABLE test_layer (
            fid INTEGER PRIMARY KEY AUTOINCREMENT,
            geom BLOB,
            name TEXT,
            address_id INTEGER,
            road_id INTEGER
        );

        INSERT INTO gpkg_contents VALUES (
            'test_layer', 'features', 'test_layer', '',
            datetime('now'), NULL, NULL, NULL, NULL, 4326
        );

        INSERT INTO gpkg_geometry_columns VALUES (
            'test_layer', 'geom', 'POINT', 4326, 0, 0
        );

        INSERT INTO test_layer (fid, name, address_id, road_id) VALUES (1, 'Point A', 1, 101);
        INSERT INTO test_layer (fid, name, address_id, road_id) VALUES (2, 'Point B', 2, 202);
        INSERT INTO test_layer (fid, name, address_id, road_id) VALUES (3, 'Point C', 3, 303);
        INSERT INTO test_layer (fid, name, address_id, road_id) VALUES (4, 'Point D', 4, 404);
        INSERT INTO test_layer (fid, name, address_id, road_id) VALUES (5, 'Point E', 5, 505);
    """)

    conn.commit()
    conn.close()

    return gpkg_path


# ============================================================================
# Legacy Fixtures (for backward compatibility during transition)
# ============================================================================


@pytest.fixture
def fake_functions_module():
    """Legacy fixture - creates a fake functions module."""
    import types

    mod = types.ModuleType("functions")

    def fake_check_output(*_a, **_kw):
        return ""

    mod.check_output = fake_check_output
    return mod


@pytest.fixture
def make_fake_actions_module():
    """Legacy fixture - creates a fake actions module factory."""
    import types

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

        context = SimpleNamespace(os=object(), repo={"name": "x"})
        core = DummyCore()

        mod.context = context
        mod.core = core
        return mod

    return _make


@pytest.fixture
def make_fake_settings_module():
    """Legacy fixture - creates a fake settings module factory."""
    import types

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
    """Legacy fixture - creates fake pygeodiff and shapely modules."""
    import types

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
    """Legacy fixture - dummy CLI runner class."""

    class DummyCliRunner:
        def invoke(self, app, args):
            return SimpleNamespace(exit_code=0, output="ok")

    return DummyCliRunner
