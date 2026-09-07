from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    paths = [TASK / "ACTIVE_CONFORMANCE_INPUT_LOCK.json", TASK / "ACTIVE_TRANSITION_CONFORMANCE_MATRIX_V2.csv", TASK / "scenario_manifest.json", TASK / "model_check_active_runtime_contract_conformance_v2.py", TASK / "validate_active_runtime_contract_conformance_v2.py"]
    paths.extend(sorted((TASK / "tests").glob("test_*.py")))
    lock = {
        "schema": "ACTIVE_CONFORMANCE_EXECUTION_LOCK_V2",
        "repository": "kenqiana04/safer-splat",
        "runtime_under_test_head": "b4ff579cf6a2bcffd0661cd39eb925aa4f3a5d27",
        "upstream_pr": 119,
        "task_branch": "validate-active-runtime-contract-conformance-v2",
        "cpu_only": True,
        "real_active_rollout_count": 0,
        "gpu_execution_count": 0,
        "scientific_oracle_count": 0,
        "official100_count": 0,
        "runtime_correction_quota": 0,
        "first_counterexample_stop": True,
        "frozen_inputs": [{"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": digest(path)} for path in paths],
    }
    (TASK / "ACTIVE_CONFORMANCE_EXECUTION_LOCK.json").write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(lock, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
