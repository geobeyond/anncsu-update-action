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
                        {
                        "column": 0,
                        "old": 28671617
                        },
                        {
                        "column": 2,
                        "old": 1222582
                        },
                        {
                        "column": 6,
                        "new": "4",
                        "old": "44"
                        }
                    ],
                    "table": "WhereAbouts_fails",
                    "type": "update"
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
                        {
                        "column": 0,
                        "old": 28671616
                        },
                        {
                        "column": 1,
                        "new": "R1AAAQAAAAABAQAAAAAAAICcwitAAAAAwInzREA=",
                        "old": "R1AAAQAAAAABAQAAAObiXKWtwitAXt3+bojzREA="
                        },
                        {
                        "column": 2,
                        "old": 1222582
                        }
                    ],
                    "table": "WhereAbouts_fails",
                    "type": "update"
                }
            ]
        }
    )


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
