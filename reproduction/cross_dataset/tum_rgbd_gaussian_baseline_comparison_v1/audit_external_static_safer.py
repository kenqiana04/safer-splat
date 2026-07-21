"""Boundary guard for static-only SAFER work; it must not instantiate any controller."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--adapter-summary", type=Path, required=True); p.add_argument("--output", type=Path, required=True); a = p.parse_args()
    state = json.loads(a.adapter_summary.read_text(encoding="utf-8")).get("status")
    result = {"status": "NOT_RUN_COMMON_ADAPTER_UNRESOLVED", "adapter_status": state,
              "controller": False, "dynamics": False, "qp": False, "trajectory": False, "navigation": False, "G1": False}
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__": main()
