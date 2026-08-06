"""Fail-closed audit of the B0-B3 method matrix at the frozen PR #84 blob."""
from __future__ import annotations

import ast
import csv
import io
import json
import subprocess

from common import sha256_bytes, write_json, write_text
from task_config import BLOCK_DECISION, BLOCK_NEXT, BLOCK_STATUS, PR84_HEAD, REPO_ROOT, TASK_ROOT

PREFIX = "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/"


def git_bytes(relative: str) -> bytes:
    return subprocess.run(["git", "show", f"{PR84_HEAD}:{PREFIX}{relative}"], cwd=REPO_ROOT, check=True, capture_output=True).stdout


def main() -> None:
    candidate_bytes = git_bytes("certifier/candidate_library.py")
    certifier_bytes = git_bytes("certifier/executable_safety_certifier.py")
    report_bytes = git_bytes("report/REPORT_IMPLEMENT_ACTUATOR_BOUNDED_SWEPT_SEGMENT_TERMINAL_BACKUP_CERTIFIER_V1.md")
    proof = json.loads(git_bytes("proof_artifacts/proof_status_registry.json"))
    candidate_tree = ast.parse(candidate_bytes.decode("utf-8"))
    certifier_tree = ast.parse(certifier_bytes.decode("utf-8"))
    module_assignments = [node for node in candidate_tree.body if isinstance(node, (ast.Assign, ast.AnnAssign))]
    control_constructors = [node for node in ast.walk(candidate_tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Control"]
    order_function = next(node for node in candidate_tree.body if isinstance(node, ast.FunctionDef) and node.name == "frozen_candidate_order")
    certify_function = next(node for node in ast.walk(certifier_tree) if isinstance(node, ast.FunctionDef) and node.name == "certify")
    certify_args = [argument.arg for argument in certify_function.args.args]
    facts = {
        "candidate_library_git_blob_sha256": sha256_bytes(candidate_bytes),
        "executable_certifier_git_blob_sha256": sha256_bytes(certifier_bytes),
        "candidate_library_module_level_assignment_count": len(module_assignments),
        "candidate_library_control_constructor_count": len(control_constructors),
        "frozen_candidate_order_arguments": [argument.arg for argument in order_function.args.args],
        "certify_arguments": certify_args,
        "alternative_controls_is_caller_supplied": "alternative_controls" in certify_args,
        "upstream_proof_candidate_library_completeness": proof.get("unresolved", {}).get("candidate_library_completeness", proof.get("candidate_library_completeness")),
        "upstream_report_marks_completeness_unresolved": b"candidate library completeness" in report_bytes,
        "concrete_alternative_acceleration_values_frozen": False,
        "concrete_alternative_candidate_ids_frozen": False,
        "alternative_library_size_frozen": False,
        "alternative_library_canonical_identity_frozen": False,
        "ordering_rule_frozen": True,
    }
    checks = {
        "shared_map_snapshot_definable": True,
        "shared_state_goal_definable": True,
        "shared_nominal_and_filtered_controls_definable": True,
        "shared_current_full_query_definable": True,
        "nested_B0_B1_B2_definable": True,
        "B3_alternative_values_frozen_by_pr84": facts["concrete_alternative_acceleration_values_frozen"],
        "B3_alternative_ids_frozen_by_pr84": facts["concrete_alternative_candidate_ids_frozen"],
        "B3_alternative_size_frozen_by_pr84": facts["alternative_library_size_frozen"],
        "B3_alternative_identity_frozen_by_pr84": facts["alternative_library_canonical_identity_frozen"],
        "no_new_scientific_input_needed": False,
    }
    fairness_pass = all(checks.values())
    status = "PASS_METHOD_FAIRNESS_CONTRACT" if fairness_pass else BLOCK_STATUS
    registry = {
        "status": status,
        "methods": [
            {"id": "B0_CURRENT_CBF_ONLY", "input": "frozen_u_filtered", "gates": ["actuator", "current_full_query"], "alternatives": False, "executable_from_frozen_inputs": True},
            {"id": "B1_PLUS_SWEPT_SEGMENT", "input": "same_frozen_u_filtered", "gates": ["actuator", "current_full_query", "swept_segment"], "alternatives": False, "executable_from_frozen_inputs": True},
            {"id": "B2_PLUS_TERMINAL_BACKUP_NO_ALTERNATIVES", "input": "same_frozen_u_filtered", "gates": ["actuator", "current_full_query", "swept_segment", "terminal_backup"], "alternatives": False, "executable_from_frozen_inputs": True},
            {"id": "B3_FULL_UNIFIED_CERTIFIER_WITH_ALTERNATIVES", "input": "nominal_existing_filtered_and_missing_concrete_task_local_alternatives", "gates": ["actuator", "current_full_query", "swept_segment", "terminal_backup", "alternative_search"], "alternatives": True, "executable_from_frozen_inputs": False},
        ],
        "frozen_order_rule": "nominal_then_existing_filtered_sorted_by_id_then_task_local_sorted_by_id_then_deterministic_braking",
        "missing_contract": ["alternative acceleration values", "alternative candidate IDs", "alternative library size", "alternative library canonical identity"],
        "prohibited_repair": "Do not invent or tune a task-local alternative set after PR #84.",
    }
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["comparison", "only_allowed_difference", "contract_status", "reason"])
    writer.writerow(["B1_vs_B0", "add_swept_segment_gate", "DEFINED", "same primary control"])
    writer.writerow(["B2_vs_B1", "add_terminal_backup_gate", "DEFINED", "same primary control"])
    writer.writerow(["B3_vs_B2", "add_frozen_alternative_search", "UNDEFINED", "PR84 freezes order but not alternative values IDs size or identity"])
    writer.writerow(["B3_vs_B0", "all_executable_safety_gates", "UNDEFINED", "B3 scientific input incomplete"])
    freeze = json.loads((TASK_ROOT / "input_freeze/pr84_identity.json").read_text(encoding="utf-8"))
    shared = {"pr84_head": PR84_HEAD, "artifact_manifest_sha256": freeze["artifact_manifest_sha256"],
              "map_identity_file_sha256": sha256_bytes((TASK_ROOT / "input_freeze/replica_map_identity.json").read_bytes()),
              "reference_identity_file_sha256": sha256_bytes((TASK_ROOT / "input_freeze/reference_mesh_identity.json").read_bytes()),
              "u_nom_u_filtered_across_methods": "REQUIRED_IDENTICAL_NOT_EXECUTED",
              "reference_online_read_count": 0}
    audit = {"status": status, "fairness_pass": fairness_pass, "checks": checks, "facts": facts,
             "blocking_reason": "PR #84 provides a deterministic ordering function over caller-supplied alternatives but does not freeze the alternative library content, IDs, size, or identity. Defining those values in this benchmark would change B3's scientific input and violate the no-library-change rule.",
             "final_status": BLOCK_STATUS, "final_decision": BLOCK_DECISION, "only_next_task": BLOCK_NEXT,
             "candidate_search_started": False, "formal_benchmark_started": False}
    write_json(TASK_ROOT / "methods/method_registry.json", registry)
    write_text(TASK_ROOT / "methods/method_difference_matrix.csv", buffer.getvalue())
    write_json(TASK_ROOT / "methods/fairness_audit.json", audit)
    write_json(TASK_ROOT / "methods/shared_input_hashes.json", shared)
    print(status)
    if not fairness_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
