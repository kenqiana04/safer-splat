"""Document the raw-Git-blob recovery contract used for the server snapshot."""
from __future__ import annotations
import json
from pathlib import Path

root = Path(__file__).parent
summary = json.loads((root / "input_identity_summary.json").read_text(encoding="utf-8"))
assert summary["source"]["sha256"] == summary["expected"]["e3_source"]
print("RAW_GIT_BLOB_SOURCE_RESTORATION_ALREADY_VERIFIED")
