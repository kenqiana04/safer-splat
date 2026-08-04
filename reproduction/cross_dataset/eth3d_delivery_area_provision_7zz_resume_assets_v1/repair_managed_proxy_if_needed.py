#!/usr/bin/env python3
"""Read-only proxy health gate; repairs require explicit managed-resource proof."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import socket
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    args = parser.parse_args()
    checked = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    reachable = False
    error = None
    try:
        with socket.create_connection(("127.0.0.1", 17898), timeout=5):
            reachable = True
    except OSError as exc:
        error = str(exc)
    result = {"checked_utc": checked, "listener": "127.0.0.1:17898", "reachable": reachable,
              "repair_attempted": False, "repair_success": False, "error": error,
              "port_17897_touched": False, "sshd_restart_count": 0, "firewall_change_count": 0}
    (args.task_root / "managed_proxy_health.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not reachable:
        raise SystemExit("MANAGED_PROXY_REPAIR_REQUIRED")
    print("PASS_MANAGED_PROXY_HEALTH_NO_REPAIR")


if __name__ == "__main__":
    main()
