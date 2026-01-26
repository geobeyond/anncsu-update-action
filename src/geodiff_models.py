from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


Primitive = Union[int, float, str, bool, None]


class Change(BaseModel):
    column: int
    old: Optional[Primitive] = Field(default=None)
    new: Optional[Primitive] = Field(default=None)


class GeodiffEntry(BaseModel):
    table: str
    type: Literal["insert", "update", "delete"]
    changes: List[Change]


class GeodiffFile(BaseModel):
    geodiff: List[GeodiffEntry]

    @classmethod
    def from_json_text(cls, text: str) -> "GeodiffFile":
        """Parse a JSON text into a GeodiffFile model."""
        data = json.loads(text)
        return cls.model_validate(data)

    @classmethod
    def from_path(cls, path: str | Path) -> "GeodiffFile":
        p = Path(path)
        text = p.read_text(encoding="utf-8")
        return cls.from_json_text(text)

    def to_json(self, **kwargs: Any) -> str:
        return self.model_dump_json(indent=2, **kwargs)

    @classmethod
    def write_json_schema(cls, out_path: str | Path) -> None:
        """Write the full JSON Schema for the GeodiffFile model to `out_path`."""
        p = Path(out_path)
        schema = cls.model_json_schema()
        p.write_text(json.dumps(schema, indent=2), encoding="utf-8")

    @classmethod
    def json_schema_for_entry_type(cls, entry_type: Literal["insert", "update", "delete"]) -> Dict[str, Any]:
        """Return a JSON Schema for GeodiffEntry constrained to a given `type` value.

        This is useful to produce three small schemas (insert/update/delete) matching
        the examples produced by geodiff.
        """
        entry_schema = GeodiffEntry.model_json_schema()
        # Ensure the `type` property is a const specific to the provided entry_type
        # Copy schema to avoid mutating internal definitions
        schema = json.loads(json.dumps(entry_schema))
        props = schema.get("properties", {})
        if "type" in props:
            props["type"] = {"const": entry_type, "type": "string"}
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": f"GeodiffEntry_{entry_type}",
            **schema,
        }

    @classmethod
    def write_entry_type_schemas(cls, out_dir: str | Path) -> None:
        p = Path(out_dir)
        p.mkdir(parents=True, exist_ok=True)
        for t in ("delete", "update", "insert"):
            schema = cls.json_schema_for_entry_type(t)
            (p / f"geodiff_entry_{t}_schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")


def validate_examples_from_strings(examples: Dict[str, str]) -> Dict[str, bool]:
    """Validate multiple example JSON texts.

    Returns a mapping of example name -> True if validates, otherwise raises and returns False.
    """
    results: Dict[str, bool] = {}
    for name, text in examples.items():
        try:
            GeodiffFile.from_json_text(text)
            results[name] = True
        except Exception:
            results[name] = False
    return results


# if __name__ == "__main__":
#     # Example CLI usage: write schemas to ./schemas and optionally validate files
#     import argparse

#     ap = argparse.ArgumentParser()
#     ap.add_argument("--out", "-o", default="schemas", help="Directory to write JSON Schema files")
#     ap.add_argument("--validate", "-v", nargs="*", help="Paths to example JSON files to validate")
#     args = ap.parse_args()

#     out_dir = Path(args.out)
#     GeodiffFile.write_json_schema(out_dir / "geodiff_file_schema.json")
#     GeodiffFile.write_entry_type_schemas(out_dir)
#     print(f"Wrote JSON Schemas to: {out_dir}")

#     if args.validate:
#         for p in args.validate:
#             ok = GeodiffFile.from_path(p)
#             print(f"Validated: {p}")
