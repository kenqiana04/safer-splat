#!/usr/bin/env python3
"""Fresh-process canonical registry rebuild worker."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))
from common import canonical_json_bytes, sha256_json


def normalized(source: dict) -> dict:
    payload = {key: value for key, value in source.items() if key != "registry_content_sha256"}
    payload["selection_locked"] = True
    payload["states"] = list(source["states"])
    payload["registry_content_sha256"] = sha256_json(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    source = json.loads(arguments.input.read_text(encoding="utf-8"))
    data = canonical_json_bytes(normalized(source)) + b"\n"
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(data)


if __name__ == "__main__":
    main()
