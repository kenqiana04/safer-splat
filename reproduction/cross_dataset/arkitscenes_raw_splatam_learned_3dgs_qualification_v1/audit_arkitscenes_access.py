#!/usr/bin/env python3
"""Read-only official endpoint and resource gate for ARKitScenes."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from arkitscenes_common import atomic_json, run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--apple-head", required=True)
    args = parser.parse_args()
    task = args.task_root.resolve()
    wrapper = Path.home() / ".config" / "scannetpp_proxy" / "run_with_scannetpp_proxy.sh"
    checks = {
        "wrapper": wrapper.is_file() and wrapper.stat().st_mode & 0o111 != 0,
        "github": run([str(wrapper), "curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "-I", "--connect-timeout", "10", "--max-time", "30", "https://github.com"]),
        "apple": run([str(wrapper), "git", "ls-remote", "https://github.com/apple/ARKitScenes.git", "HEAD"], timeout=45),
        "splatam": run([str(wrapper), "git", "ls-remote", "https://github.com/spla-tam/SplaTAM.git", "HEAD"], timeout=45),
        "download_script": run([str(wrapper), "curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "-I", "--connect-timeout", "10", "--max-time", "30", f"https://raw.githubusercontent.com/apple/ARKitScenes/{args.apple_head}/download_data.py"]),
        "disk_free_bytes": shutil.disk_usage("/disk1/zlab").free,
    }
    passed = bool(checks["wrapper"]) and all(str(checks[name]["stdout_tail"]).strip() == "200" if name in {"github", "download_script"} else checks[name]["returncode"] == 0 for name in ("github", "apple", "splatam", "download_script")) and checks["disk_free_bytes"] >= 250 * 1024**3
    status = "PASS" if passed else "BLOCKED_BY_ARKITSCENES_OFFICIAL_DOWNLOAD_ACCESS"
    atomic_json(task / "access" / "arkitscenes_access_preflight.json", {"status": status, "checks": checks, "download_count": 0, "training_count": 0, "controller_benchmark_count": 0})
    print(status)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
