#!/usr/bin/env python3
"""Reflectively validate the V4-C helper symbols discovered by AST audit."""

from __future__ import annotations

import argparse
import csv
import importlib
import inspect
from pathlib import Path
from typing import Any


FIELDS = (
    "provider_module",
    "symbol",
    "exists",
    "symbol_kind",
    "signature",
    "source_file",
    "source_line",
    "semantic_role",
    "required_for_shadow_m2",
    "passed",
    "notes",
)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def symbol_kind(value: Any) -> str:
    if inspect.isclass(value):
        return "class"
    if inspect.isfunction(value):
        return "function"
    if callable(value):
        return "callable"
    return type(value).__name__


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    inventory = read_rows(args.inventory)
    modules: dict[str, Any] = {}
    output: list[dict[str, Any]] = []
    failed = False
    for row in inventory:
        provider = row["provider_module"]
        module = modules.setdefault(provider, importlib.import_module(provider))
        name = row["symbol"]
        exists = hasattr(module, name)
        value = getattr(module, name, None)
        required = row["required_for_shadow_m2"].lower() == "true"
        passed = exists or not required
        failed = failed or not passed
        signature = ""
        source_file = ""
        source_line: int | str = ""
        if exists:
            try:
                signature = str(inspect.signature(value))
            except (TypeError, ValueError):
                signature = "not_applicable"
            try:
                source_file = inspect.getsourcefile(value) or ""
                source_line = inspect.getsourcelines(value)[1]
            except (OSError, TypeError):
                source_line = ""
        output.append(
            {
                "provider_module": provider,
                "symbol": name,
                "exists": str(exists).lower(),
                "symbol_kind": symbol_kind(value) if exists else "missing",
                "signature": signature,
                "source_file": source_file,
                "source_line": source_line,
                "semantic_role": row["semantic_role"],
                "required_for_shadow_m2": row["required_for_shadow_m2"],
                "passed": str(passed).lower(),
                "notes": "Required list loaded from AST-generated inventory.",
            }
        )
    write_rows(args.output, output)
    print(f"symbols={len(output)} failed={sum(row['passed'] != 'true' for row in output)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
