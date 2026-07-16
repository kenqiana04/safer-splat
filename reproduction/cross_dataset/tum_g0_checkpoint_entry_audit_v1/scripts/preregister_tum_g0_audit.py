#!/usr/bin/env python3
"""Verify that the committed preregistration exists before audit execution."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
required = [ROOT / "README.md", ROOT / "G0_PROTOCOL_PREREGISTRATION.md", ROOT / "G0_GATE_REGISTRY.json"]
missing = [str(p) for p in required if not p.is_file()]
if missing:
    raise SystemExit("missing preregistration artifacts: " + ", ".join(missing))
registry = json.loads((ROOT / "G0_GATE_REGISTRY.json").read_text(encoding="utf-8"))
if registry.get("preregistration_state") != "committed_before_asset_inspection":
    raise SystemExit("preregistration state is not committed_before_asset_inspection")
print("preregistration_ready")
