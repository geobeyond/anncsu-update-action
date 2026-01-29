import sys
from pathlib import Path

import json


# Ensure src is on sys.path for imports
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from geodiff_models import GeodiffFile, validate_examples_from_strings  # noqa: E402 (because nee to import after path insert)
# JSON example fixtures moved to tests/conftest.py as pytest fixtures:
# - geodiff_delete_json
# - geodiff_update_json
# - geodiff_insert_json


def test_parse_delete(geodiff_delete_json):
    g = GeodiffFile.from_json_text(geodiff_delete_json)
    assert len(g.geodiff) == 1
    entry = g.geodiff[0]
    assert entry.type == "delete"
    assert entry.table == "simple"
    assert len(entry.changes) == 4
    assert entry.changes[0].column == 0
    assert entry.changes[0].old == 2


def test_parse_update(geodiff_update_json):
    g = GeodiffFile.from_json_text(geodiff_update_json)
    entry = g.geodiff[0]
    assert entry.type == "update"
    # second change has both old and new
    change1 = entry.changes[1]
    assert change1.old == "R1AAAeYQAAABAQAAAPBDGq/kSde/+HS2Feb94T8="
    assert change1.new == "R1AAAeYQAAABAQAAAMp+uos0te2/hISLbYZyzj8="
    # third change numeric update
    change2 = entry.changes[2]
    assert change2.old == 2
    assert change2.new == 9999


def test_parse_insert(geodiff_insert_json):
    g = GeodiffFile.from_json_text(geodiff_insert_json)
    entry = g.geodiff[0]
    assert entry.type == "insert"
    assert entry.changes[0].new == 4
    assert entry.changes[2].new == "my new point A"


def test_write_entry_type_schemas_and_validate(tmp_path):
    # write schemas to tmp_path
    GeodiffFile.write_entry_type_schemas(tmp_path)
    # ensure files exist
    for t in ("delete", "update", "insert"):
        p = tmp_path / f"geodiff_entry_{t}_schema.json"
        assert p.exists()
        data = json.loads(p.read_text(encoding="utf-8"))
        # top-level title includes the type
        assert data.get("title") == "GeodiffEntry"


def test_validate_examples_from_strings(geodiff_delete_json, geodiff_update_json, geodiff_insert_json):
    results = validate_examples_from_strings(
        {"delete": geodiff_delete_json, "update": geodiff_update_json, "insert": geodiff_insert_json}
    )
    assert all(results.values())


def test_roundtrip_to_json(geodiff_insert_json):
    g = GeodiffFile.from_json_text(geodiff_insert_json)
    s = g.to_json()
    g2 = GeodiffFile.from_json_text(s)
    assert g.model_dump() == g2.model_dump()


def test_from_path_and_from_json_text(tmp_path, geodiff_insert_json):
    p = tmp_path / "example.json"
    p.write_text(geodiff_insert_json, encoding="utf-8")
    g = GeodiffFile.from_path(p)
    assert isinstance(g, GeodiffFile)
    assert g.geodiff[0].type == "insert"


def test_write_json_schema(tmp_path):
    out = tmp_path / "geodiff_file_schema.json"
    GeodiffFile.write_json_schema(out)
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "geodiff" in data.get("properties", {})


def test_json_schema_for_entry_type():
    schema = GeodiffFile.json_schema_for_entry_type("update")
    assert schema.get("title") == "GeodiffEntry"
    props = schema.get("properties", {})
    assert props.get("type", {}).get("const") == "update"


def test_validate_examples_invalid():
    results = validate_examples_from_strings({"bad": "{not: json"})
    assert results.get("bad") is False
