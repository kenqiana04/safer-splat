"""Run three fresh server generator-only processes and compare canonical state identities."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

TASK_ROOT = Path(__file__).resolve().parents[1]
if str(TASK_ROOT) not in sys.path:
    sys.path.insert(0, str(TASK_ROOT))

from common import write_json
from task_config import MAP_ROOT, ROUTE_REGISTRY, SERVER, SERVER_TASK_ROOT, START_REGISTRY


def main() -> None:
    remote_script = f"{SERVER_TASK_ROOT}/smoke/run_generator_only_replica_smoke.py"
    remote_paths = [f"{SERVER_TASK_ROOT}/smoke/generator_determinism_process_{index}.json" for index in range(1, 4)]
    for path in remote_paths:
        command = f"set -eu; export PYTHONDONTWRITEBYTECODE=1; export PYTHONNOUSERSITE=1; python3 -B {remote_script} --map-root {MAP_ROOT} --route-registry {ROUTE_REGISTRY} --start-registry {START_REGISTRY} --output {path}"
        subprocess.run(["ssh", SERVER, command], check=True)
    values = []
    for index, remote in enumerate(remote_paths, 1):
        local = TASK_ROOT / f"smoke/generator_determinism_process_{index}.json"
        subprocess.run(["scp", "-q", f"{SERVER}:{remote}", str(local)], check=True)
        values.append(json.loads(local.read_text(encoding="utf-8"))["state_candidate_identity_aggregate_sha256"])
    result = {"status": "PASS_REPLICA_SMOKE_THREE_PROCESS_DETERMINISM" if len(set(values)) == 1 else "BLOCKED_BY_ALTERNATIVE_LIBRARY_NONDETERMINISM", "process_count": 3, "mismatch_count": max(0, len(set(values)) - 1), "aggregate_sha256_values": values}
    write_json(TASK_ROOT / "smoke/three_process_determinism.json", result)
    if result["mismatch_count"]:
        raise SystemExit(result["status"])
    print(result["status"], values[0])


if __name__ == "__main__":
    main()
