#!/usr/bin/env python3

# Anncsu Update Action
# This action extracts specified tables from a DuckDB database file
# and saves them in the desired format (GPKG or Parquet).
# two versions of the table are extracted: current and previous (if available)
# where previous refers to the version in the previous commit.

import json
import base64
from pathlib import Path
from typer.testing import CliRunner
from shapely import wkb, Point

from actions import context, core

import functions
from geodiff_models import GeodiffFile, GeodiffEntry
from pygeodiff import GeoDiff
from settings import AnncsuUpdateSettings

from anncsu.cli import app

version: str = core.get_version()
core.info(f"Starting Anncsu Update Action - \033[32;1m{version}")


# Inputs

geodiff_report: str = core.get_input("geodiff_report", True)
core.info(f"geodiff_report: \033[36;1m{geodiff_report}")
token: str = core.get_input("token", True)

# Debug

with core.group("uv"):
    functions.check_output("uv -V", False)
    functions.check_output("uv python dir", False)


ctx = {k: v for k, v in vars(context).items() if not k.startswith("__")}
del ctx["os"]
with core.group("GitHub Context Data"):
    core.debug(json.dumps(ctx, indent=4))


# Action Logic

core.info("Update ANNCU DB from geodiff report...")


def _call_anncsu_cli_for_entry(entry: GeodiffEntry) -> bool:
    """Placeholder to call the ANNCSU CLI for a single GeodiffEntry.
    a generic entry shold have the following attributes:
    - type: str (insert/update/delete)
    - table: str
    - changes: list of changes (dicts)
    Returns True if the call was successful, False otherwise.

    # columns: 0: address_id (AKA PROGRESSIVO_ACCESSO)
    # columns: 2: road_id (AKA PROGRESSIVO_NAZIONALE)
    # column: 1: coordinate (AKA COORDINATE)
    Example entry:{
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
                        "column": 1,
                        "new": "R1AAAQAAAAABAQAAAAAAAICcwitAAAAAwInzREA=",
                        "old": "R1AAAQAAAAABAQAAAObiXKWtwitAXt3+bojzREA="
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
    """
    # try:
    action = entry.type
    table = entry.table

    # find address_id and road_id from changes because PKs
    # BTW only address_id is strictly required for ANNCSU operations
    address_id = None
    road_id = None
    gpkg_geom = None

    for change in entry.changes:
        if change.column == 0:
            address_id = change.new or change.old
        if change.column == 2:
            road_id = change.new or change.old
        elif change.column == 1:
            gpkg_geom = change.new or change.old

    # convert gpkg_geom to shapely geometry and extract x,y
    if gpkg_geom:
        decoded_gpkg_geom = base64.b64decode(gpkg_geom)
        geodiff = GeoDiff()
        wkb_geom = geodiff.create_wkb_from_gpkg_header(decoded_gpkg_geom)[0]
        geometry = wkb.loads(wkb_geom)

        # check geom is valid
        if not geometry.is_valid:
            core.warn(f"Invalid geometry for address_id={address_id}, road_id={road_id}")
            return False

        # check geometry is Point
        if geometry.geom_type != "Point":
            core.warn(f"Geometry is not a Point for address_id={address_id}, road_id={road_id}")
            return False

        # cast geometry to point
        coord = list(geometry.coords)[0]
        point = Point(coord)

        x, y = point.x, point.y
        core.info(f"Extracted coordinates: x={x}, y={y}")
    else:
        x, y = None, None
        core.warn(f"No geometry found for address_id={address_id}, road_id={road_id}; skipping anncsu update")
        return False

    core.info(f"Preparing ANNCSU CLI call: action={action} table={table} address_id={address_id} road_id={road_id}")
    # TODO: implement real ANNCSU CLI calls (insert/update/delete)
    # Example placeholder behaviour:
    if action == "insert":
        core.info(f"Insert {len(entry.changes)} values into {table}")
    elif action == "update":
        core.info(f"Update {len(entry.changes)} column values in {table} with PK: address_id={address_id}")

        result = cli_runner.invoke(
            app,
            [
                "coordinate",
                "update",
                "--codcom",
                settings.codice_comune,
                "--progr-civico",
                str(address_id) if address_id else "",
                "--x",
                str(x),
                "--y",
                str(y),
                "--metodo",
                "4",
            ],
        )
        if result.exit_code != 0:
            core.error(f"ANNCSU CLI coordinate update failed: {result.output} - exit code {result.exit_code}")
            return False
        core.info(f"ANNCSU CLI coordinate update succeeded: {result.output}")

    elif action == "delete":
        core.info(f"Delete {len(entry.changes)} values from {table}")
    else:
        core.warn(f"Unknown action type: {action}")
        return False
    return True
    # except Exception as exc:  # pragma: no cover - defensive
    #     core.error(f"Error calling ANNCSU CLI for entry: {exc}")
    #     return False


# load settings
core.info("Loading Anncsu Update Settings...")
try:
    settings = AnncsuUpdateSettings()
    core.debug(f"Loaded settings: {settings.model_dump_json()}")
except Exception as exc:
    core.set_failed(f"Failed to load Anncsu Update Settings: {exc}")
    raise SystemExit(1) from exc

# notify what code is being used
core.info(f"Using codice_comune: \033[36;1m{settings.codice_comune}\033[0m")

# Load and validate the geodiff report
report_path = Path(geodiff_report)
geodiff_obj = None
try:
    if report_path.exists():
        core.info(f"Found geodiff report file: {report_path}")
        try:
            geodiff_obj = GeodiffFile.from_path(report_path)
        except Exception as exc:
            core.error(f"Failed to parse geodiff report file: {exc}")
    else:
        core.info("geodiff_report input does not point to a file; attempting to parse as JSON text")
        try:
            geodiff_obj = GeodiffFile.from_json_text(geodiff_report)
        except Exception as exc:
            core.error(f"Failed to parse geodiff_report input as JSON: {exc}")
except Exception:
    core.warn("Can't open geodiff_report as file, try as json")
    try:
        geodiff_obj = GeodiffFile.from_json_text(geodiff_report)
    except Exception as exc:
        core.error(f"Failed to parse geodiff_report input as JSON: {exc}")

if geodiff_obj is None:
    core.set_failed("Could not load or validate geodiff report; aborting")
    raise SystemExit(1)

# then authenticate with ANNCSU CLI
core.info("Authenticating with ANNCSU CLI...")
cli_runner = CliRunner()
TEST_CLI_TYPE = "pa"
try:
    result = cli_runner.invoke(app, ["auth", "login", "--api", TEST_CLI_TYPE])
    if result.exit_code != 0:
        raise RuntimeError(f"{result.output}")
except Exception as exc:
    core.set_failed(f"Failed to authenticate with ANNCSU CLI: {exc}")
    raise SystemExit(1) from exc

# instantiate anncsu sdk client
core.info("ANNCSU CLI update basing on geodiff report JSON...")
try:
    # Dispatch entries to ANNCSU CLI handlers
    results = []
    for entry in geodiff_obj.geodiff:
        ok = _call_anncsu_cli_for_entry(entry)
        results.append((entry.type, ok))

    success = all(r for _, r in results)
    if not success:
        core.warn("One or more ANNCSU CLI calls failed (see logs)")

    # Track temp files for cleanup
    temp_files_to_cleanup: list[str] = []

except Exception as exc:
    core.set_failed(f"Failed to instantiate ANNCSU SDK client: {exc}")
    raise SystemExit(1) from exc

# Initialize variables


core.info("Anncsu Update Action completed")
print("\033[32;1mAnncsu Update Action completed successfully\033[0m")
