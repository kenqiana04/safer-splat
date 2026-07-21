"""Verify the tracked frozen-input summary without touching remote inputs."""
from __future__ import annotations
import json
from pathlib import Path

root = Path(__file__).parent
summary = json.loads((root / "input_identity_summary.json").read_text(encoding="utf-8"))
assert summary["status"] == "PASS" and summary["all_match"]
print("INPUT_IDENTITY_PASS")
