#!/usr/bin/env python3
"""Fail-closed, token-safe ScanNet++ official-access preflight."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path


OFFICIAL_URLS = {
    "toolbox": "https://github.com/scannetpp/scannetpp.git",
    "demo": "https://github.com/scannetpp/3DGS-demo.git",
    "toolbox_web": "https://github.com/scannetpp/scannetpp",
}


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def command_status(command: list[str], timeout_seconds: int) -> dict[str, object]:
    try:
        completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   timeout=timeout_seconds, check=False)
        return {"returncode": completed.returncode, "timed_out": False,
                "stdout_tail": completed.stdout[-500:], "stderr_tail": completed.stderr[-500:]}
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True, "stdout_tail": "", "stderr_tail": ""}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    args = parser.parse_args()
    task_root = args.task_root.resolve()
    dns = {}
    for host in ("github.com", "huggingface.co"):
        try:
            dns[host] = sorted({item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
        except OSError as error:
            dns[host] = {"error": type(error).__name__}
    token_names = sorted(name for name in os.environ if any(part in name.upper() for part in
                         ("SCANNET", "DOWNLOAD_TOKEN", "SCANNETPP")))
    git = command_status(["git", "ls-remote", "--symref", OFFICIAL_URLS["toolbox"], "HEAD"], 20)
    curl = command_status(["curl", "-L", "-sS", "-o", "/dev/null", "-w", "%{http_code}",
                           "--connect-timeout", "8", "--max-time", "15", OFFICIAL_URLS["toolbox_web"]], 20)
    asset_root_present = args.asset_root.exists()
    remote_reachable = git["returncode"] == 0 and not git["timed_out"] and curl["returncode"] == 0 and curl["stdout_tail"] == "200"
    status = "PASS" if asset_root_present or remote_reachable else "BLOCKED_BY_SCANNETPP_OFFICIAL_ACCESS"
    result = {
        "status": status,
        "checked_unix_s": time.time(),
        "official_urls": OFFICIAL_URLS,
        "dns": dns,
        "git_ls_remote": git,
        "https_probe": curl,
        "asset_root_present": asset_root_present,
        "token_environment_variable_names": token_names,
        "token_values_recorded": False,
        "interpretation": "Only official authority is acceptable; timeout/no local official asset fails closed.",
        "next_task": "RESUME_SCANNETPP_AFTER_OFFICIAL_ACCESS_V1" if status != "PASS" else None,
    }
    atomic_json(task_root / "access" / "access_preflight.json", result)
    atomic_json(task_root / "authority" / "scannetpp_authority_identity.json", {
        "status": status,
        "dataset_version_required": "v2",
        "official_urls": OFFICIAL_URLS,
        "toolbox_commit": None,
        "demo_commit": None,
        "reason": "Official repositories were not cloned because access preflight did not pass." if status != "PASS" else None,
    })
    atomic_json(task_root / "run_manifest.json", {
        "task": "SCANNETPP_LEARNED_3DGS_EXTERNAL_QUALIFICATION_V1",
        "phase": "official_access_preflight",
        "status": status,
        "official_download_bytes": 0,
        "official_training_attempts": 0,
        "controller_benchmark_count": 0,
        "next_task": result["next_task"],
    })
    print(json.dumps({"status": status, "access_record": str(task_root / "access" / "access_preflight.json")}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
