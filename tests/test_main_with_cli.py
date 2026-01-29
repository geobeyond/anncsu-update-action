import importlib
import sys
from pathlib import Path
import typer.testing
from geodiff_models import GeodiffFile


def test_main_with_report_as_file(
    monkeypatch,
    geodiff_real_coord_update_json,
    make_fake_actions_module,
    make_fake_settings_module,
    make_fake_pygeodiff_and_shapely,
    DummyCliRunner,
    fake_functions_module,
    tmp_path,
):
    # use provided fixture JSON with a valid geometry
    geodiff_json = geodiff_real_coord_update_json
    geodiff_report = tmp_path / "geodiff_report.json"
    geodiff_report.write_text(geodiff_json, encoding="utf-8")

    # insert src on path for imports
    ROOT = Path(__file__).resolve().parents[1]
    SRC = ROOT / "src"
    sys.path.insert(0, str(SRC))

    # inject fake modules to avoid side effects during import
    monkeypatch.setitem(sys.modules, "actions", make_fake_actions_module(geodiff_report))
    monkeypatch.setitem(sys.modules, "settings", make_fake_settings_module())
    pygeodiff_mod, shapely_mod = make_fake_pygeodiff_and_shapely()
    monkeypatch.setitem(sys.modules, "pygeodiff", pygeodiff_mod)
    monkeypatch.setitem(sys.modules, "shapely", shapely_mod)
    monkeypatch.setitem(sys.modules, "shapely.wkb", shapely_mod.wkb)
    monkeypatch.setitem(sys.modules, "functions", fake_functions_module)
    # stub typer.testing.CliRunner so CLI auth doesn't execute external code
    monkeypatch.setattr(typer.testing, "CliRunner", DummyCliRunner)

    # Now import the module under test; module-level code should run without side effects
    # and exceptions
    if "main_with_cli" in sys.modules:
        del sys.modules["main_with_cli"]
    importlib.import_module("main_with_cli")


def test_main_with_report_as_json(
    monkeypatch,
    geodiff_real_coord_update_json,
    make_fake_actions_module,
    make_fake_settings_module,
    make_fake_pygeodiff_and_shapely,
    DummyCliRunner,
    fake_functions_module,
):
    # use provided fixture JSON with a valid geometry
    geodiff_json = geodiff_real_coord_update_json

    # insert src on path for imports
    ROOT = Path(__file__).resolve().parents[1]
    SRC = ROOT / "src"
    sys.path.insert(0, str(SRC))

    # inject fake modules to avoid side effects during import
    monkeypatch.setitem(sys.modules, "actions", make_fake_actions_module(geodiff_json))
    monkeypatch.setitem(sys.modules, "settings", make_fake_settings_module())
    pygeodiff_mod, shapely_mod = make_fake_pygeodiff_and_shapely()
    monkeypatch.setitem(sys.modules, "pygeodiff", pygeodiff_mod)
    monkeypatch.setitem(sys.modules, "shapely", shapely_mod)
    monkeypatch.setitem(sys.modules, "shapely.wkb", shapely_mod.wkb)
    monkeypatch.setitem(sys.modules, "functions", fake_functions_module)
    # stub typer.testing.CliRunner so CLI auth doesn't execute external code
    monkeypatch.setattr(typer.testing, "CliRunner", DummyCliRunner)

    # Now import the module under test; module-level code should run without side effects
    # and exceptions
    if "main_with_cli" in sys.modules:
        del sys.modules["main_with_cli"]
    importlib.import_module("main_with_cli")


def test_call_anncsu_cli_for_entry_success(
    monkeypatch,
    geodiff_real_coord_update_json,
    make_fake_actions_module,
    make_fake_settings_module,
    make_fake_pygeodiff_and_shapely,
    DummyCliRunner,
    fake_functions_module,
):
    # use provided fixture JSON with a valid geometry
    geodiff_json = geodiff_real_coord_update_json

    # insert src on path for imports
    ROOT = Path(__file__).resolve().parents[1]
    SRC = ROOT / "src"
    sys.path.insert(0, str(SRC))

    # inject fake modules to avoid side effects during import
    monkeypatch.setitem(sys.modules, "actions", make_fake_actions_module(geodiff_json))
    monkeypatch.setitem(sys.modules, "settings", make_fake_settings_module())
    pygeodiff_mod, shapely_mod = make_fake_pygeodiff_and_shapely()
    monkeypatch.setitem(sys.modules, "pygeodiff", pygeodiff_mod)
    monkeypatch.setitem(sys.modules, "shapely", shapely_mod)
    monkeypatch.setitem(sys.modules, "shapely.wkb", shapely_mod.wkb)
    monkeypatch.setitem(sys.modules, "functions", fake_functions_module)
    # stub typer.testing.CliRunner so CLI auth doesn't execute external code
    monkeypatch.setattr(typer.testing, "CliRunner", DummyCliRunner)

    # Now import the module under test; module-level code should run without side effects
    if "main_with_cli" in sys.modules:
        del sys.modules["main_with_cli"]
    mod = importlib.import_module("main_with_cli")

    # construct a synthetic entry to call the function directly from fixture
    geodiffReport = GeodiffFile.from_json_text(geodiff_json)
    entry = geodiffReport.geodiff[0]

    result = mod._call_anncsu_cli_for_entry(entry)
    assert result is True


def test_call_anncsu_cli_for_entry_missing_geometry(
    monkeypatch,
    geodiff_real_value_update_json,
    make_fake_actions_module,
    make_fake_settings_module,
    make_fake_pygeodiff_and_shapely,
    DummyCliRunner,
    fake_functions_module,
):
    # use provided fixture JSON where geometry column may be absent
    geodiff_json = geodiff_real_value_update_json

    ROOT = Path(__file__).resolve().parents[1]
    SRC = ROOT / "src"
    sys.path.insert(0, str(SRC))

    monkeypatch.setitem(sys.modules, "actions", make_fake_actions_module(geodiff_json))
    monkeypatch.setitem(sys.modules, "settings", make_fake_settings_module())
    pygeodiff_mod, shapely_mod = make_fake_pygeodiff_and_shapely()
    monkeypatch.setitem(sys.modules, "pygeodiff", pygeodiff_mod)
    monkeypatch.setitem(sys.modules, "shapely", shapely_mod)
    monkeypatch.setitem(sys.modules, "shapely.wkb", shapely_mod.wkb)
    monkeypatch.setitem(sys.modules, "functions", fake_functions_module)
    # stub typer.testing.CliRunner so CLI auth doesn't execute external code
    monkeypatch.setattr(typer.testing, "CliRunner", DummyCliRunner)

    if "main_with_cli" in sys.modules:
        del sys.modules["main_with_cli"]
    mod = importlib.import_module("main_with_cli")

    # build entry from fixture
    geodiffReport = GeodiffFile.from_json_text(geodiff_json)
    entry = geodiffReport.geodiff[0]

    result = mod._call_anncsu_cli_for_entry(entry)
    assert result is False
