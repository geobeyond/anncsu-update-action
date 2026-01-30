#!/usr/bin/env python3

# Anncsu Update Action
# This action extracts specified tables from a DuckDB database file
# and saves them in the desired format (GPKG or Parquet).
# two versions of the table are extracted: current and previous (if available)
# where previous refers to the version in the previous commit.

from __future__ import annotations

import json
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Any, runtime_checkable

from geodiff_models import GeodiffFile, GeodiffEntry


# ============================================================================
# Protocol definitions for dependency injection
# ============================================================================


@runtime_checkable
class LoggerProtocol(Protocol):
    """Protocol for logging operations."""

    def get_version(self) -> str: ...
    def info(self, message: str) -> None: ...
    def debug(self, message: str) -> None: ...
    def warn(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...
    def set_failed(self, message: str) -> None: ...
    def group(self, name: str) -> Any: ...
    def get_input(self, name: str, required: bool = False) -> str: ...


@runtime_checkable
class SettingsProtocol(Protocol):
    """Protocol for settings."""

    codice_comune: str

    def model_dump_json(self) -> str: ...


@runtime_checkable
class CliRunnerProtocol(Protocol):
    """Protocol for CLI runner."""

    def invoke(self, app: Any, args: list[str]) -> Any: ...


@runtime_checkable
class GeoDiffProtocol(Protocol):
    """Protocol for GeoDiff operations."""

    def create_wkb_from_gpkg_header(self, data: bytes) -> list[bytes]: ...


@runtime_checkable
class GeometryProtocol(Protocol):
    """Protocol for geometry objects."""

    is_valid: bool
    geom_type: str
    coords: Any


# ============================================================================
# Data classes for structured results
# ============================================================================


@dataclass
class Coordinates:
    """Represents extracted X,Y coordinates."""

    x: float
    y: float


@dataclass
class EntryResult:
    """Result of processing a single geodiff entry."""

    entry_type: str
    success: bool
    error_message: str | None = None


# ============================================================================
# Geometry parsing functions (now separately testable)
# ============================================================================


def decode_gpkg_geometry(
    gpkg_base64: str,
    geodiff: GeoDiffProtocol,
    wkb_loader: Any,
) -> GeometryProtocol:
    """Decode a base64-encoded GPKG geometry to a shapely geometry.

    Args:
        gpkg_base64: Base64-encoded GPKG geometry header
        geodiff: GeoDiff instance for WKB conversion
        wkb_loader: shapely.wkb.loads function

    Returns:
        Decoded shapely geometry object

    Raises:
        ValueError: If geometry cannot be decoded
    """
    decoded_gpkg_geom = base64.b64decode(gpkg_base64)
    wkb_geom = geodiff.create_wkb_from_gpkg_header(decoded_gpkg_geom)[0]
    return wkb_loader(wkb_geom)


def extract_coordinates_from_geometry(
    geometry: GeometryProtocol,
    point_class: Any,
) -> Coordinates:
    """Extract X,Y coordinates from a Point geometry.

    Args:
        geometry: Shapely geometry object
        point_class: shapely.Point class for coordinate extraction

    Returns:
        Coordinates object with x,y values

    Raises:
        ValueError: If geometry is invalid or not a Point
    """
    if not geometry.is_valid:
        raise ValueError("Invalid geometry")

    if geometry.geom_type != "Point":
        raise ValueError(f"Geometry is not a Point, got: {geometry.geom_type}")

    coord = list(geometry.coords)[0]
    point = point_class(coord)
    return Coordinates(x=point.x, y=point.y)


def parse_gpkg_to_coordinates(
    gpkg_base64: str,
    geodiff: GeoDiffProtocol,
    wkb_loader: Any,
    point_class: Any,
) -> Coordinates:
    """Parse a GPKG geometry string to X,Y coordinates.

    This is the main entry point for geometry parsing, combining
    decode and coordinate extraction.

    Args:
        gpkg_base64: Base64-encoded GPKG geometry
        geodiff: GeoDiff instance
        wkb_loader: shapely.wkb.loads function
        point_class: shapely.Point class

    Returns:
        Coordinates object

    Raises:
        ValueError: If parsing fails
    """
    geometry = decode_gpkg_geometry(gpkg_base64, geodiff, wkb_loader)
    return extract_coordinates_from_geometry(geometry, point_class)


# ============================================================================
# Entry processing functions
# ============================================================================


def extract_entry_data(entry: GeodiffEntry) -> tuple[int | None, int | None, str | None]:
    """Extract address_id, road_id, and geometry from a geodiff entry.

    Args:
        entry: GeodiffEntry to process

    Returns:
        Tuple of (address_id, road_id, gpkg_geom)
    """
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

    return address_id, road_id, gpkg_geom


def process_entry(
    entry: GeodiffEntry,
    settings: SettingsProtocol,
    cli_runner: CliRunnerProtocol,
    cli_app: Any,
    geodiff: GeoDiffProtocol,
    wkb_loader: Any,
    point_class: Any,
    logger: LoggerProtocol,
) -> bool:
    """Process a single geodiff entry and call the ANNCSU CLI.

    Args:
        entry: GeodiffEntry to process
        settings: Application settings
        cli_runner: CLI runner instance
        cli_app: ANNCSU CLI app
        geodiff: GeoDiff instance for geometry conversion
        wkb_loader: shapely.wkb.loads function
        point_class: shapely.Point class
        logger: Logger for output

    Returns:
        True if processing succeeded, False otherwise
    """
    action = entry.type
    table = entry.table

    address_id, road_id, gpkg_geom = extract_entry_data(entry)

    # Parse geometry if present
    if gpkg_geom:
        try:
            coords = parse_gpkg_to_coordinates(gpkg_geom, geodiff, wkb_loader, point_class)
            x, y = coords.x, coords.y
            logger.info(f"Extracted coordinates: x={x}, y={y}")
        except ValueError as e:
            logger.warn(f"Geometry error for address_id={address_id}, road_id={road_id}: {e}")
            return False
    else:
        logger.warn(f"No geometry found for address_id={address_id}, road_id={road_id}; skipping anncsu update")
        return False

    logger.info(f"Preparing ANNCSU CLI call: action={action} table={table} address_id={address_id} road_id={road_id}")

    if action == "insert":
        logger.info(f"Insert {len(entry.changes)} values into {table}")
        # TODO: implement insert CLI call
        return True

    elif action == "update":
        logger.info(f"Update {len(entry.changes)} column values in {table} with PK: address_id={address_id}")

        result = cli_runner.invoke(
            cli_app,
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
            logger.error(f"ANNCSU CLI coordinate update failed: {result.output} - exit code {result.exit_code}")
            return False
        logger.info(f"ANNCSU CLI coordinate update succeeded: {result.output}")
        return True

    elif action == "delete":
        logger.info(f"Delete {len(entry.changes)} values from {table}")
        # TODO: implement delete CLI call
        return True

    else:
        logger.warn(f"Unknown action type: {action}")
        return False


def process_all_entries(
    geodiff_file: GeodiffFile,
    settings: SettingsProtocol,
    cli_runner: CliRunnerProtocol,
    cli_app: Any,
    geodiff: GeoDiffProtocol,
    wkb_loader: Any,
    point_class: Any,
    logger: LoggerProtocol,
) -> list[EntryResult]:
    """Process all entries in a geodiff file.

    Args:
        geodiff_file: Parsed geodiff file
        settings: Application settings
        cli_runner: CLI runner instance
        cli_app: ANNCSU CLI app
        geodiff: GeoDiff instance
        wkb_loader: shapely.wkb.loads function
        point_class: shapely.Point class
        logger: Logger for output

    Returns:
        List of EntryResult objects
    """
    results = []
    for entry in geodiff_file.geodiff:
        success = process_entry(
            entry=entry,
            settings=settings,
            cli_runner=cli_runner,
            cli_app=cli_app,
            geodiff=geodiff,
            wkb_loader=wkb_loader,
            point_class=point_class,
            logger=logger,
        )
        results.append(EntryResult(entry_type=entry.type, success=success))
    return results


# ============================================================================
# Geodiff report loading
# ============================================================================


def load_geodiff_report(geodiff_report: str, logger: LoggerProtocol) -> GeodiffFile | None:
    """Load a geodiff report from file path or JSON text.

    Args:
        geodiff_report: File path or JSON text
        logger: Logger for output

    Returns:
        Parsed GeodiffFile or None if loading failed
    """
    report_path = Path(geodiff_report)
    geodiff_obj = None

    try:
        if report_path.exists():
            logger.info(f"Found geodiff report file: {report_path}")
            try:
                geodiff_obj = GeodiffFile.from_path(report_path)
            except Exception as exc:
                logger.error(f"Failed to parse geodiff report file: {exc}")
        else:
            logger.info("geodiff_report input does not point to a file; attempting to parse as JSON text")
            try:
                geodiff_obj = GeodiffFile.from_json_text(geodiff_report)
            except Exception as exc:
                logger.error(f"Failed to parse geodiff_report input as JSON: {exc}")
    except Exception:
        logger.warn("Can't open geodiff_report as file, try as json")
        try:
            geodiff_obj = GeodiffFile.from_json_text(geodiff_report)
        except Exception as exc:
            logger.error(f"Failed to parse geodiff_report input as JSON: {exc}")

    return geodiff_obj


# ============================================================================
# CLI Authentication
# ============================================================================


def authenticate_cli(
    cli_runner: CliRunnerProtocol,
    cli_app: Any,
    api_type: str,
    logger: LoggerProtocol,
) -> bool:
    """Authenticate with the ANNCSU CLI.

    Args:
        cli_runner: CLI runner instance
        cli_app: ANNCSU CLI app
        api_type: API type for authentication (e.g., "pa")
        logger: Logger for output

    Returns:
        True if authentication succeeded, False otherwise
    """
    logger.info("Authenticating with ANNCSU CLI...")
    try:
        result = cli_runner.invoke(cli_app, ["auth", "login", "--api", api_type])
        if result.exit_code != 0:
            logger.error(f"CLI authentication failed: {result.output}")
            return False
        return True
    except Exception as exc:
        logger.error(f"Failed to authenticate with ANNCSU CLI: {exc}")
        return False


# ============================================================================
# Main function
# ============================================================================


def run_action(
    geodiff_report: str,
    settings: SettingsProtocol,
    cli_runner: CliRunnerProtocol,
    cli_app: Any,
    geodiff: GeoDiffProtocol,
    wkb_loader: Any,
    point_class: Any,
    logger: LoggerProtocol,
    api_type: str = "pa",
) -> bool:
    """Run the ANNCSU update action.

    This is the main entry point for the action, designed for testability
    via dependency injection.

    Args:
        geodiff_report: File path or JSON text of the geodiff report
        settings: Application settings
        cli_runner: CLI runner instance
        cli_app: ANNCSU CLI app
        geodiff: GeoDiff instance
        wkb_loader: shapely.wkb.loads function
        point_class: shapely.Point class
        logger: Logger for output
        api_type: API type for CLI authentication

    Returns:
        True if action completed successfully, False otherwise
    """
    logger.info("Update ANNCSU DB from geodiff report...")
    logger.info(f"Using codice_comune: \033[36;1m{settings.codice_comune}\033[0m")

    # Load geodiff report
    geodiff_obj = load_geodiff_report(geodiff_report, logger)
    if geodiff_obj is None:
        logger.set_failed("Could not load or validate geodiff report; aborting")
        return False

    # Authenticate with CLI
    if not authenticate_cli(cli_runner, cli_app, api_type, logger):
        logger.set_failed("Failed to authenticate with ANNCSU CLI")
        return False

    # Process all entries
    logger.info("ANNCSU CLI update based on geodiff report JSON...")
    results = process_all_entries(
        geodiff_file=geodiff_obj,
        settings=settings,
        cli_runner=cli_runner,
        cli_app=cli_app,
        geodiff=geodiff,
        wkb_loader=wkb_loader,
        point_class=point_class,
        logger=logger,
    )

    success = all(r.success for r in results)
    if not success:
        logger.warn("One or more ANNCSU CLI calls failed (see logs)")

    logger.info("Anncsu Update Action completed")
    return success


# ============================================================================
# Module-level execution (for GitHub Action)
# ============================================================================


def main() -> None:
    """Main entry point when running as a GitHub Action."""
    # Import dependencies only when running as main
    from typer.testing import CliRunner
    from shapely import wkb, Point
    from pygeodiff import GeoDiff

    from actions import context, core
    import functions
    from settings import AnncsuUpdateSettings
    from anncsu.cli import app

    # Log startup
    version: str = core.get_version()
    core.info(f"Starting Anncsu Update Action - \033[32;1m{version}")

    # Get inputs
    geodiff_report: str = core.get_input("geodiff_report", True)
    core.info(f"geodiff_report: \033[36;1m{geodiff_report}")
    _token: str = core.get_input("token", True)  # noqa: F841

    # Debug info
    with core.group("uv"):
        functions.check_output("uv -V", False)
        functions.check_output("uv python dir", False)

    ctx = {k: v for k, v in vars(context).items() if not k.startswith("__")}
    del ctx["os"]
    with core.group("GitHub Context Data"):
        core.debug(json.dumps(ctx, indent=4))

    # Load settings
    core.info("Loading Anncsu Update Settings...")
    try:
        settings = AnncsuUpdateSettings()
        core.debug(f"Loaded settings: {settings.model_dump_json()}")
    except Exception as exc:
        core.set_failed(f"Failed to load Anncsu Update Settings: {exc}")
        raise SystemExit(1) from exc

    # Create CLI runner
    cli_runner = CliRunner()

    # Run the action
    success = run_action(
        geodiff_report=geodiff_report,
        settings=settings,
        cli_runner=cli_runner,
        cli_app=app,
        geodiff=GeoDiff(),
        wkb_loader=wkb.loads,
        point_class=Point,
        logger=core,
        api_type="pa",
    )

    if success:
        print("\033[32;1mAnncsu Update Action completed successfully\033[0m")
    else:
        raise SystemExit(1)


# Only execute when running directly, not when importing
if __name__ == "__main__":
    main()
