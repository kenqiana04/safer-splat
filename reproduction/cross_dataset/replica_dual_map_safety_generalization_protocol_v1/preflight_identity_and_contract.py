#!/usr/bin/env python3
"""Read-only preflight guard for the Replica dual-map protocol.

It intentionally refuses to create a route registry when the required formal
robot bounds are absent.  This prevents a desired-command clip from being
misrepresented as a physical or QP-output bound.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED = {
    "mesh": "274677d9b7caa413230363b68f4aa472e5cc1afe87e422a489fa1b7d844c6182",
    "navmesh": "32296d6457d3855ffe172cf1970364559def5dd15892e149b44d0bc7c6b7e938",
    "contract": "ddd147f908537165c40a34b412cd21c3cbfb5a0615871375d02adecbbfaec6f7",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v3-contract", type=Path, required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--navmesh", type=Path, required=True)
    parser.add_argument("--robot-contract", type=Path, required=True)
    args = parser.parse_args()

    observed = {
        "contract": sha256(args.v3_contract),
        "mesh": sha256(args.mesh),
        "navmesh": sha256(args.navmesh),
    }
    if observed != EXPECTED:
        raise SystemExit(f"BLOCKED_BY_REPLICA_DUAL_MAP_INPUT_IDENTITY_MISMATCH: {observed}")

    contract = json.loads(args.robot_contract.read_text(encoding="utf-8"))
    missing = contract.get("missing_required_formal_fields", {})
    if contract.get("status") != "PASS" or missing:
        raise SystemExit("BLOCKED_BY_REPLICA_ROBOT_CONTRACT_AMBIGUITY")

    required = ("vmax", "umax", "r_robot_m", "epsilon_base_m", "dt_s")
    if any(contract.get(key) is None for key in required):
        raise SystemExit("BLOCKED_BY_REPLICA_ROBOT_CONTRACT_AMBIGUITY")
    print("PRE_ROUTE_PREFLIGHT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
