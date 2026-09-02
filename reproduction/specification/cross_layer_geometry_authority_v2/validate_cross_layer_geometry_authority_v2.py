from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
UPSTREAM = "a60665f3e29085cc18f1ee03828198074f52e4f0"
EXPECTED_CONSUMERS = {
    "CONTROLLER_ACTIVE_CBF", "I0A_INITIAL_ADMISSION", "I0B_REPAIR_VERIFICATION",
    "R0_DIAGNOSTIC_CURRENT", "L1_IMMEDIATE_CLOSED_SEGMENT",
    "C0_ADMISSIBILITY_NONCONSUMER", "L2_H1_SEGMENT", "L3_BACKUP_SEGMENTS",
    "L3_TERMINAL_POINT", "L3_TERMINAL_ZERO_HOLD", "L5_TERMINAL_POINT",
    "L5_TERMINAL_ZERO_HOLD", "L4_PROPOSAL_NONCONSUMER",
    "SUPERVISOR_ARBITRATION_NONCONSUMER",
}


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

    lock = load("GEOMETRY_AUTHORITY_INPUT_LOCK.json")
    contract = load("CROSS_LAYER_GEOMETRY_AUTHORITY_V2.json")
    execution = load("GEOMETRY_AUTHORITY_EXECUTION_LOCK.json")
    reuse = load("LEGACY_GEOMETRY_REUSE_POLICY_V2.json")
    compatibility = load("METHOD_LOGIC_COMPATIBILITY_CHECK.json")
    invariants = load("CROSS_LAYER_GEOMETRY_INVARIANTS_V2.json")

    check(lock["pr107"]["head"] == UPSTREAM, "PR107 exact identity", checks)
    input_ok = all(hashlib.sha256(raw_blob(x["path"])).hexdigest() == x["sha256"] for x in lock["input_blobs"])
    check(input_ok, "all input raw Git blobs exact", checks)
    changed = [p for p in run("git", "diff", "--name-only", UPSTREAM, "HEAD").splitlines() if p]
    check(all(p.startswith("reproduction/specification/cross_layer_geometry_authority_v2/") for p in changed), "task-local diff only", checks)
    check(not any(p in {"run.py", "cbf/cbf_utils.py"} for p in changed), "controller and runtime source unchanged", checks)
    check(not any(p.startswith("reproduction/design/l0_controller_geometry_contract_v2/") for p in changed), "PR106 artifacts unchanged", checks)
    check(not any(p.startswith("reproduction/specification/method_logic_closure_v2/") for p in changed), "PR107 artifacts unchanged", checks)
    check(not any("fas_cbf_unified_executable_safety_certifier_v1" in p or "l2_h1_shadow_certifier_v1" in p for p in changed), "historical V1 artifacts unchanged", checks)

    check(contract["controller"]["radius_m"] == 0.015 and contract["controller"]["runtime_change"] is False, "controller G0 exact and unchanged", checks)
    check(contract["margin"]["margin_m"] == 0.01 and contract["composition"]["margin_application_count"] == 1, "G1 margin exact and single application", checks)
    check(contract["composition"]["certification_effective_radius_m"] == 0.025, "canonical certification radius exact", checks)
    check(contract["segment_reserve"]["rho_seg_m"] == 0.0 and contract["segment_reserve"]["independent_from_margin"], "G2 segment reserve exact", checks)
    check(contract["map"]["identity_required"] and contract["map"]["snapshot_mutability"] == "STATIC_IMMUTABLE", "G3 immutable map authority", checks)
    check(contract["failure_semantics"]["v1_fallback_allowed"] is False, "no historical fallback", checks)
    canonical = (json.dumps(contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
    raw_contract = (TASK / "CROSS_LAYER_GEOMETRY_AUTHORITY_V2.json").read_bytes()
    check(raw_contract == canonical, "canonical raw-byte contract encoding", checks)
    check(hashlib.sha256(raw_contract).hexdigest() == execution["canonical_contract_sha256"], "execution-lock contract SHA", checks)
    check(execution["design_commit"] == run("git", "rev-parse", "HEAD~0") or execution["design_commit"] == run("git", "rev-parse", "HEAD~1"), "execution lock binds design commit", checks)

    with (TASK / "GEOMETRY_CONSUMER_INVENTORY_V2.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    by_layer = {r["layer"]: r for r in rows}
    check(set(by_layer) == EXPECTED_CONSUMERS, "consumer inventory complete", checks)
    cert_rows = [r for r in rows if r["authority_status"] == "RESOLVED" and r["layer"] != "CONTROLLER_ACTIVE_CBF"]
    check(all(r["effective_radius"] == "0.025" for r in cert_rows), "all certification consumers use 0.025", checks)
    check(by_layer["CONTROLLER_ACTIVE_CBF"]["effective_radius"] == "0.015", "controller inventory remains 0.015", checks)
    check(all(r["rho_seg"] == "0.0" for r in rows if r["point_or_segment"] == "segment"), "all segment consumers use rho 0", checks)
    check(all(r["map_authority"] == "STATIC_IMMUTABLE_REPRESENTED_GAUSSIAN_MAP_AUTHORITY" for r in rows if r["authority_status"] == "RESOLVED"), "all geometry consumers use G3", checks)

    check(reuse["v1_011_invalidated"] is False and reuse["default_unresolved_behavior"] == "UNKNOWN_BLOCK_NO_FALLBACK", "legacy quarantine preserves V1 and blocks fallback", checks)
    check(compatibility["compatibility"] == "PASS" and compatibility["r0_role"] == "CHEAP_DIAGNOSTIC_OR_HEALTH_PRECHECK_ONLY", "method logic compatibility", checks)
    check(len(invariants["invariants"]) >= 10, "cross-layer invariants complete", checks)
    check(execution["synthetic_test_count"] == 10, "execution lock freezes exactly ten tests", checks)
    check(execution["runtime_execution_count"] == 0 and execution["rollout_count"] == 0 and execution["gpu_execution_count"] == 0, "no runtime rollout or GPU execution", checks)

    passed = sum(c["status"] == "PASS" for c in checks)
    result = {
        "check_count": len(checks),
        "checks": checks,
        "failed_count": len(checks) - passed,
        "passed_count": passed,
        "status": "PASS_CROSS_LAYER_GEOMETRY_AUTHORITY_V2_VALIDATION" if passed == len(checks) else "FAIL_CROSS_LAYER_GEOMETRY_AUTHORITY_V2_VALIDATION",
    }
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
