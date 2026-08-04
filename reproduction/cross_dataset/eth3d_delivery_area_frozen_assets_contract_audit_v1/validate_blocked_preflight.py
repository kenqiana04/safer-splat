#!/usr/bin/env python3
"""Validate the fail-closed ETH3D asset-audit preflight record."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main() -> None:
    preflight = load("preflight/runtime_preflight.json")
    manifest = load("run_manifest.json")
    validation = load("validation_result.json")
    assets = load("input_freeze/frozen_asset_manifest.json")

    assert preflight["server"]["disk_gate_pass"] is True
    assert preflight["archive_runtime"]["gate_pass"] is False
    assert preflight["archive_runtime"]["installation_attempted"] is False
    assert preflight["final_status"] == "BLOCKED_BY_7Z_RUNTIME_UNAVAILABLE"
    assert len(assets["whitelist"]) == 9
    assert len(assets["denylist"]) == 5
    assert sum(item["content_length"] for item in assets["whitelist"]) == 2435222146
    assert manifest["final_status"] == preflight["final_status"]
    assert validation["final_status"] == preflight["final_status"]

    counters = manifest["counters"]
    for key, value in counters.items():
        assert value == 0, f"expected zero counter: {key}={value}"

    print("PASS_BLOCKED_PREFLIGHT_RECORD_CONSISTENT")


if __name__ == "__main__":
    main()
