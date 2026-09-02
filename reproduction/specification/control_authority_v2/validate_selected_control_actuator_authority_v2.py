from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
UPSTREAM = "f04a2077c4f483f20696bb5515c576cd75ddf449"
PR107 = "a60665f3e29085cc18f1ee03828198074f52e4f0"


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=REPO, text=True).strip()


def load(name: str):
    return json.loads((TASK / name).read_text(encoding="utf-8"))


def raw_blob(path: str) -> bytes:
    return subprocess.check_output(["git", "cat-file", "blob", f"{UPSTREAM}:{path}"], cwd=REPO)


def check(condition: bool, label: str, checks: list[dict]) -> None:
    checks.append({"check": label, "status": "PASS" if condition else "FAIL"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(TASK / "validation_result.json"))
    args = parser.parse_args()
    checks: list[dict] = []
    lock = load("CONTROL_AUTHORITY_INPUT_LOCK.json")
    contract = load("SELECTED_CONTROL_ACTUATOR_CONTRACT_V2.json")
    graph = load("CONTROL_AUTHORITY_GRAPH_V2.json")
    invariants = load("CONTROL_AUTHORITY_INVARIANTS_V2.json")
    execution = load("CONTROL_AUTHORITY_EXECUTION_LOCK.json")

    check(lock["pr108"]["head"] == UPSTREAM and lock["pr107"]["head"] == PR107, "upstream PR107 and PR108 identities exact", checks)
    check(all(hashlib.sha256(raw_blob(x["path"])).hexdigest() == x["sha256"] for x in lock["input_blobs"]), "all input raw Git blobs exact", checks)
    changed = [p for p in run("git", "diff", "--name-only", UPSTREAM, "HEAD").splitlines() if p]
    check(all(p.startswith("reproduction/specification/control_authority_v2/") for p in changed), "task-local diff only", checks)
    check(not any(p in {"run.py", "cbf/cbf_utils.py", "dynamics/systems.py"} for p in changed), "controller QP and dynamics untouched", checks)
    check(not any(p.startswith("reproduction/specification/cross_layer_geometry_authority_v2/") for p in changed), "geometry authority untouched", checks)
    check(not any(p.startswith("reproduction/specification/method_logic_closure_v2/") for p in changed), "method logic untouched", checks)
    check(not any("fas_cbf_unified_executable_safety_certifier_v1" in p for p in changed), "historical certifier untouched", checks)

    check(len(graph["current_frozen_simulation_edges"]) == 5 and len(graph["target_v2_edges"]) == 4, "authority graph complete", checks)
    check(contract["execution_control"]["current_frozen_simulation_relation"] == "u_executed == u_selected == successful u_cbf", "selected executed relation explicit", checks)
    check(contract["execution_control"]["transformation_allowed"] is False, "no hidden post-certification transformation", checks)
    bounds = contract["actuator_authority"]["bounds"]
    check(bounds["u_min"] == [-0.1] * 3 and bounds["u_max"] == [0.1] * 3 and bounds["inclusive"] is True, "actuator contract complete", checks)
    check(contract["actuator_authority"]["physical_hardware_authority"] == "OUTSIDE_METHOD_BOUNDARY_UNKNOWN", "physical actuator boundary explicit", checks)
    check(contract["policies"]["unknown_handling"] == "BLOCK_NO_SILENT_PASS_NO_FALLBACK", "unknown handling fail closed", checks)
    check(contract["backup_compatibility"]["all_backup_controls_require_same_actuator_admission"], "backup actuator consistency", checks)
    check(contract["terminal_compatibility"]["terminal_zero_control_requires_same_actuator_admission"], "terminal actuator consistency", checks)
    ids = {x["id"] for x in invariants["invariants"]}
    check({f"CTRL-{i:02d}" for i in range(1, 11)}.issubset(ids), "required invariants present", checks)
    check(invariants["runtime_implementation_authority"] is False, "runtime implementation authority false", checks)
    canonical = (json.dumps(contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
    raw_contract = (TASK / "SELECTED_CONTROL_ACTUATOR_CONTRACT_V2.json").read_bytes()
    check(raw_contract == canonical, "canonical raw-byte contract encoding", checks)
    check(hashlib.sha256(raw_contract).hexdigest() == execution["canonical_contract_sha256"], "execution lock binds contract SHA", checks)
    check(execution["design_commit"] in {run("git", "rev-parse", "HEAD"), run("git", "rev-parse", "HEAD~1")}, "execution lock binds design commit", checks)
    check(execution["synthetic_test_count"] == 10, "exactly ten synthetic tests frozen", checks)
    check(all(execution[k] == 0 for k in ("runtime_mutation_count", "controller_mutation_count", "dynamics_mutation_count", "rollout_count", "gpu_execution_count")), "runtime controller dynamics rollout GPU counts zero", checks)

    passed = sum(x["status"] == "PASS" for x in checks)
    result = {
        "check_count": len(checks),
        "checks": checks,
        "failed_count": len(checks) - passed,
        "passed_count": passed,
        "status": "PASS_SELECTED_CONTROL_ACTUATOR_AUTHORITY_V2_FREEZE" if passed == len(checks) else "FAIL_SELECTED_CONTROL_ACTUATOR_AUTHORITY_V2_FREEZE",
    }
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
