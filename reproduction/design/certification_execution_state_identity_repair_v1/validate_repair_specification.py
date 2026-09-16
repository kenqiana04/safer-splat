#!/usr/bin/env python3
"""CPU-only validator for the specification freeze. It executes no runtime path."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


BASE = "50cadfe614da70ce0345c4b1789c787dc529287e"
BRANCH = "freeze-certification-execution-state-identity-repair-spec-v1"
TASK = Path("reproduction/design/certification_execution_state_identity_repair_v1")
EXPECTED_LOCKS = {
    "near_zero_result_lock_sha256": "4811693c02005af44b81a9405090ec49e31dfc490ca54ad596bcd7973c1736f7",
    "semantic_gap_result_lock_sha256": "cb3d45a536d5f8407e5647b8514535e55584ff879f24da23da24873d748f61ea",
    "continuity_result_lock_sha256": "af521fed9153f93490495a3b52add88c039926c6b1d7a50e56f70f101b6e8b78",
}
REQUIRED = {
    "README.md",
    "REPAIR_SPECIFICATION.md",
    "REPAIR_SPECIFICATION.json",
    "ROOT_CAUSE_EVIDENCE_LOCK.json",
    "PREDICTED_STATE_CONSTRUCTION_INVENTORY.csv",
    "NORMATIVE_INVARIANTS.md",
    "PROOF_OBLIGATIONS.md",
    "IMPLEMENTATION_CHANGE_PLAN.md",
    "VALIDATION_PLAN.md",
    "MIGRATION_MATRIX.csv",
    "DOWNSTREAM_HANDOFF.json",
    "DRAFT_PR_BODY.md",
    "validate_repair_specification.py",
}


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def load_json(name: str):
    return json.loads((TASK / name).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))

    record("branch_exact", git("branch", "--show-current") == BRANCH)
    record("base_ancestor", subprocess.run(["git", "merge-base", "--is-ancestor", BASE, "HEAD"]).returncode == 0)
    record("required_files", REQUIRED.issubset({p.name for p in TASK.iterdir() if p.is_file()}))

    status_paths = []
    status_output = subprocess.run(
        ["git", "status", "--porcelain"], text=True, stdout=subprocess.PIPE, check=True
    ).stdout
    for line in status_output.splitlines():
        if line:
            status_paths.append(line[3:].split(" -> ")[-1])
    allowed_prefix = TASK.as_posix() + "/"
    record("working_tree_scope", all(p.replace("\\", "/").startswith(allowed_prefix) for p in status_paths), repr(status_paths))

    diff_paths = git("diff", "--name-only", BASE, "--").splitlines()
    record("protected_source_diff_zero", all(p.startswith(allowed_prefix) for p in diff_paths), repr(diff_paths))

    lock = load_json("ROOT_CAUSE_EVIDENCE_LOCK.json")
    spec = load_json("REPAIR_SPECIFICATION.json")
    handoff = load_json("DOWNSTREAM_HANDOFF.json")
    record("authority_base_exact", lock["runtime_authority_head"] == BASE and spec["authority_base"]["head"] == BASE)
    record("root_cause_exact", lock["closed_root_cause"] == "COMMON_FLOAT32_REALIZATION_IDENTITY_GAP")
    record("frozen_failure_preserved", lock["frozen_scientific_result"] == "FAIL_V3_HARD_SAFETY_GATE" and spec["frozen_scientific_result"] == "FAIL_V3_HARD_SAFETY_GATE")
    record("four_trials_exact", lock["active_hard_violation_trial_ids"] == [22, 28, 57, 59] and spec["archived_offline_trials"] == [22, 28, 57, 59])
    record("paired_counts_preserved", lock["frozen_paired_trials"] == 85 and lock["reference_hard_violation_count"] == 0)

    evidence = lock["diagnostic_evidence"]
    record("diagnostic_locks_exact", all(evidence[k] == v for k, v in EXPECTED_LOCKS.items()))
    commits = ["6a134d5", "445769f", "1f1aff2", "026ed9e", "bada56a"]
    record("diagnostic_commits_exist", all(subprocess.run(["git", "cat-file", "-e", f"{c}^{{commit}}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0 for c in commits))
    source_hashes = lock["relevant_runtime_source_sha256"]
    record("runtime_source_hashes_exact", len(source_hashes) >= 13 and all(Path(path).is_file() and sha256(Path(path)) == expected for path, expected in source_hashes.items()))

    geometry = spec["frozen_geometry"]
    record("geometry_unchanged", geometry == {
        "hard_radius_q": 0.015,
        "runtime_margin_q": 0.0,
        "rho_seg_q": 0.0,
        "historical_diagnostic_radius_q": 0.025,
        "historical_diagnostic_runtime_authority": False,
    })
    record("execution_counts_zero", all(v == 0 for v in spec["execution_counts"].values()))
    record("canonical_transition_pure", spec["canonical_transition"]["pure"] and not spec["canonical_transition"]["side_effects"] and spec["canonical_transition"]["must_match_actual_plant_bitwise"])
    record("l1_candidate_independent", spec["l1"]["candidate_independent"] and spec["l1"]["action_independence_requires_bitwise_proof"])
    record("l2_sequential", spec["l2"]["construction"] == "SEQUENTIAL_CANONICAL_TRANSITIONS" and spec["l2"]["host_binary64_closed_form_forbidden"])
    record("mismatch_fail_closed", not spec["mismatch_semantics"]["pass_allowed"] and not spec["mismatch_semantics"]["commit_authority_allowed"])
    record("proof_obligations_complete", spec["proof_obligations"] == [f"PO{i}" for i in range(1, 11)])
    record("handoff_base_not_diagnostic", handoff["implementation_base_head"] == BASE and not handoff["diagnostic_branch_as_implementation_base_allowed"])
    record("only_next_task", handoff["only_next_task"] == "IMPLEMENT_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_V1")

    normative = (TASK / "NORMATIVE_INVARIANTS.md").read_text(encoding="utf-8")
    repair = (TASK / "REPAIR_SPECIFICATION.md").read_text(encoding="utf-8")
    obligations = (TASK / "PROOF_OBLIGATIONS.md").read_text(encoding="utf-8")
    record("continuity_invariant_present", "CERTIFICATION_EXECUTION_CONTINUITY_INVARIANT_V1" in normative and "bitwise" in normative)
    record("identity_statuses_present", all(x in repair for x in ("CERT_EXEC_STATE_IDENTITY_MATCH", "CERT_EXEC_STATE_IDENTITY_MISMATCH")))
    record("all_po_documented", all(f"PO{i}" in obligations for i in range(1, 11)))
    record("policy_boundaries_present", all(x in repair for x in ("0.015 q", "0.025 q", "Supervisor", "PlantCommitAdapter")))

    with (TASK / "PREDICTED_STATE_CONSTRUCTION_INVENTORY.csv").open(newline="", encoding="utf-8") as f:
        inventory = list(csv.DictReader(f))
    with (TASK / "MIGRATION_MATRIX.csv").open(newline="", encoding="utf-8") as f:
        migration_reader = csv.DictReader(f)
        migration_fields = set(migration_reader.fieldnames or [])
        migration = list(migration_reader)
    record("inventory_coverage", len(inventory) >= 18 and all(row["component"] for row in inventory))
    required_migration_fields = {
        "component", "current behavior", "required behavior", "source file",
        "expected code owner", "policy change? YES/NO",
        "arithmetic identity change? YES/NO", "evidence schema change? YES/NO",
        "test obligation",
    }
    record("migration_coverage", len(migration) >= 15 and required_migration_fields == migration_fields and all(row["test obligation"] for row in migration))

    validator_text = Path(__file__).read_text(encoding="utf-8")
    parsed = ast.parse(validator_text)
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(parsed)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(name=node.module or "")])
    }
    record("validator_cpu_only", imported.isdisjoint({"torch", "cupy"}))

    failed = [item for item in checks if not item[1]]
    result = {
        "schema": "CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_SPEC_VALIDATION_V1",
        "status": "PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_SPECIFICATION_VALIDATION" if not failed else "FAIL_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_SPECIFICATION_VALIDATION",
        "check_count": len(checks),
        "failed_checks": [{"name": n, "detail": d} for n, _, d in failed],
        "task_file_sha256": {p.name: sha256(p) for p in sorted(TASK.iterdir()) if p.is_file() and p.name != "validation_result.json"},
        "runtime_implementation_count": 0,
        "gpu_count": 0,
        "trial_count": 0,
        "experiment_count": 0,
    }
    (TASK / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"])
    if failed:
        for name, _, detail in failed:
            print(f"FAIL {name}: {detail}")
        return 1
    print(f"checks={len(checks)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
