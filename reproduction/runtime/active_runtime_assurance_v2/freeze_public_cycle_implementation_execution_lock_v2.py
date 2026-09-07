from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
EVIDENCE = PACKAGE / "public_cycle_implementation_evidence"
UPSTREAM = "4148e671128444d357ea33f6e5c15d0dd2928411"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    paths = [
        PACKAGE / "active_cycle.py",
        PACKAGE / "runtime_types.py",
        PACKAGE / "supervisor.py",
        PACKAGE / "model_check_public_cycle_implementation_v2.py",
        PACKAGE / "validate_active_runtime_public_cycle_composition_v2.py",
        PACKAGE / "freeze_public_cycle_implementation_execution_lock_v2.py",
        EVIDENCE / "EXECUTABLE_TRANSITION_IMPLEMENTATION_MAP_V2.csv",
        EVIDENCE / "generate_executable_transition_implementation_map_v2.py",
        EVIDENCE / "build_public_cycle_implementation_evidence_v2.py",
    ]
    paths.extend(sorted((PACKAGE / "tests").glob("test_public_cycle*.py")))
    paths.extend((
        PACKAGE / "tests/test_supervisor_route_transition.py",
        PACKAGE / "tests/test_transition_exact_one_lookup.py",
        PACKAGE / "tests/test_bypass_semantics_preserved.py",
        PACKAGE / "tests/test_existing_runtime_regression.py",
        PACKAGE / "tests/public_cycle_test_support.py",
    ))
    lock = {
        "schema": "PUBLIC_CYCLE_IMPLEMENTATION_EXECUTION_LOCK_V2",
        "pr121_head": UPSTREAM,
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip(),
        "correction_policy": {
            "allowed_after_lock": "at_most_one_implementation_conformance_correction",
            "design_change_allowed": False,
            "real_execution_allowed": False,
        },
        "locked_files": [
            {"path": item.relative_to(REPO).as_posix(), "sha256": sha(item), "size": item.stat().st_size}
            for item in paths
        ],
        "counts": {
            "real_active": 0,
            "gpu": 0,
            "smoke": 0,
            "scientific_oracle": 0,
            "official100": 0,
            "real_bypass_pair": 0,
        },
    }
    target = EVIDENCE / "PUBLIC_CYCLE_IMPLEMENTATION_EXECUTION_LOCK.json"
    target.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("PUBLIC_CYCLE_IMPLEMENTATION_EXECUTION_LOCK_SHA256=" + sha(target))


if __name__ == "__main__":
    main()
