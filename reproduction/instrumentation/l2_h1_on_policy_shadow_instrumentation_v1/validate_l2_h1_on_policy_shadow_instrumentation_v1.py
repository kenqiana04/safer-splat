"""Fail-closed validator for implementation/static/unit/fault evidence only."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import jsonschema

from frozen_certifier_adapter import deterministic_test_adapter
from future_equivalence_runner import build_dry_run_manifest
from immutable_payload import build_immutable_payload
from map_authority import MapAuthorityFreezer
from mock_zero_authority_harness import run_fault_matrix
from observer_health import HealthEvent, HealthStatus
from reachability_capture import baseline_commit_facts


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
AUDIT = ROOT / "audit"
EXPECTED_STATUS = "PASS_L2_H1_ON_POLICY_SHADOW_INSTRUMENTATION_V1_VALIDATION"


class Validator:
    def __init__(self) -> None:
        self.checks: list[str] = []
        self.errors: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        (self.checks if condition else self.errors).append(message)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True)


def validate_schemas(v: Validator) -> None:
    schemas = {path.stem: load(path) for path in (ROOT / "schemas").glob("*.json")}
    as_json = lambda value: json.loads(json.dumps(value, allow_nan=False, sort_keys=True))
    payload = build_immutable_payload(
        run_id="validator", trial_id="validator", step_id=0, payload_sequence_id=0,
        x_k=(0, 0, 0, 0, 0, 0), dt=0.05,
        selected_u=(0.1, 0, 0), u_des=(0.2, 0, 0),
        selected_candidate_id="selected", selected_candidate_source="FROZEN_QP",
        map_authority_id="a" * 64, reachability=baseline_commit_facts(True),
    )
    jsonschema.validate(as_json(payload.capture_record()), schemas["step_payload.schema"])
    result = deterministic_test_adapter().evaluate(payload).to_record()
    result.update(
        run_id=payload.run_id, trial_id=payload.trial_id, step_id=payload.step_id,
        state_sequence_id=payload.state_sequence_id, decision_commit_id=payload.decision_commit_id,
        payload_sequence_id=payload.payload_sequence_id,
        selected_candidate_id=payload.selected_candidate.candidate_id,
        candidate_group_id=payload.candidate_group_id, map_authority_id=payload.map_authority_id,
        payload_enqueue_semantic_hash=payload.semantic_hash,
        payload_worker_receive_semantic_hash=payload.semantic_hash,
    )
    jsonschema.validate(as_json(result), schemas["shadow_result.schema"])
    jsonschema.validate(
        as_json(HealthEvent(HealthStatus.WORKER_EXCEPTION, 0, payload.decision_commit_id, "unit").to_record()),
        schemas["health_event.schema"],
    )
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "map.bin").write_bytes(b"validator-map")
        manifest = MapAuthorityFreezer().freeze(
            root=root, artifacts=["map.bin"], logical_map_name="VALIDATOR_MAP",
            representation_contract="UNIT_ONLY", robot_radius=0.015,
            safety_margin=0.0, effective_radius=0.015, rho_seg=0.0,
        )
        jsonschema.validate(as_json(manifest.to_record()), schemas["map_authority.schema"])
    jsonschema.validate(as_json(build_dry_run_manifest()), schemas["future_equivalence_manifest.schema"])
    v.require(len(schemas) == 5, "all five implementation schemas validate representative records")


def main() -> int:
    v = Validator()
    identity = load(AUDIT / "frozen_upstream_identity.json")
    protected = load(AUDIT / "protected_forbidden_source_audit.json")
    cycle = load(AUDIT / "control_cycle_identity.json")
    seam = load(AUDIT / "decision_commit_seam.json")
    delta = load(AUDIT / "approved_production_delta.json")
    roles = load(AUDIT / "u_des_candidate_role_audit.json")
    immutable = load(AUDIT / "payload_immutability_audit.json")
    hashes = load(AUDIT / "payload_hash_audit.json")
    map_audit = load(AUDIT / "map_authority_audit.json")
    side_effects = load(AUDIT / "l0_l1_l2_side_effect_audit.json")
    zero = load(AUDIT / "zero_feedback_static_audit.json")
    no_collection = load(AUDIT / "no_collection_audit.json")
    manifest = load(ROOT / "run_manifest.json")

    v.require(identity["status"] == "PASS_UPSTREAM_PR96_EXACT_IDENTITY", "PR #96 exact GitHub/local/remote identity")
    v.require(identity["upstream_pr_count"] == 12 and identity["all_expected_heads_match"], "PRs #83-#96 preserved at expected heads")
    v.require(protected["protected_blob_count"] == 17 and protected["all_raw_objects_match"], "17 protected raw blobs, sizes, and modes match")
    v.require(protected["run_py_forbidden_or_protected"] and protected["forbidden_source_mutation_count"] == 0, "run.py forbidden boundary preserved")
    v.require(not any(ROOT.rglob("run.py")), "no copied controller run.py in task root")
    v.require(delta["production_delta"] == "NONE_REQUIRED" and delta["production_source_diff_count"] == 0, "approved production delta is NONE_REQUIRED")
    v.require(seam["post_commit"] and seam["pre_plant"] and seam["fallback_used"], "wrapper seam is post-commit/pre-plant")
    v.require(cycle["selected_u_source"]["role"] == "SELECTED_EXECUTED_CONTROL", "selected u source and role frozen")
    v.require(cycle["u_des_source"]["role"] == "NOMINAL_REFERENCE", "u_des role frozen")
    v.require(roles["u_des_native_alternative_count"] == 0 and roles["synthetic_candidate_generation_count"] == 0, "u_des is never native alternative and no candidates synthesized")
    v.require(immutable["live_torch_reference_in_payload"] is False and immutable["live_numpy_reference_in_payload"] is False, "deep immutable copy has no live tensor/array references")
    v.require(hashes["enqueue_receive_equality_tested"], "canonical payload enqueue/receive hash equality tested")
    v.require(map_audit["map_authority_hash_full_call_count_per_run"] == 1 and map_audit["per_step_full_map_hash_count"] == 0, "map full hash once per run and never per step")
    v.require(side_effects["status"].startswith("PASS") and side_effects["read_only_certifier_test_count"] >= 2, "frozen certifier/read-only worker input audit")
    v.require(zero["result_return_channel_count"] == 0 and not zero["forbidden_identifier_hits"], "static AST/API audit proves zero result return")

    wrapper_text = (ROOT / "instrumented_cbf_wrapper.py").read_text(encoding="utf-8")
    transport_text = (ROOT / "nonblocking_transport.py").read_text(encoding="utf-8")
    worker_text = (ROOT / "shadow_worker.py").read_text(encoding="utf-8")
    v.require("selected_u = self._inner.solve_QP" in wrapper_text and "return selected_u" in wrapper_text, "wrapper delegates exact solve_QP and returns exact result")
    v.require("put_nowait" in transport_text and ".put(" not in transport_text, "bounded controller enqueue uses put_nowait only")
    v.require("join(" not in wrapper_text and "result(" not in wrapper_text, "no per-step wait or Future.result")
    v.require("append_result" in worker_text and "return result" not in worker_text, "worker is append-only with no controller result return")
    v.require("SHADOW_RECOMPUTED_FROZEN_CERTIFIER" in (ROOT / "frozen_certifier_adapter.py").read_text(encoding="utf-8"), "L0/L1 shadow recomputation provenance explicit")

    validate_schemas(v)
    faults = run_fault_matrix()
    v.require(faults["fault_injection_case_count"] == 10 and faults["all_fault_expectations_met"], "F1-F10 fault expectations pass")
    v.require(faults["all_mock_control_traces_equal"], "all fault mock controller traces exactly equal disabled trace")
    v.require(all(no_collection[key] == 0 for key in (
        "real_navigation_equivalence_run_count", "logging_pilot_run_count",
        "formal_on_policy_cohort_count", "on_policy_research_collection_count", "navigation_rollout_count",
    )), "real equivalence, pilot, cohort, research collection, navigation counts are zero")
    v.require(all(manifest["counts"][key] == 0 for key in (
        "controller_intervention_count", "candidate_replacement_count", "actual_fail_close_from_shadow_count",
        "L3_implementation_count", "L4_implementation_count", "L5_implementation_count", "H2_implementation_count",
        "formal_runtime_metric_count", "formal_performance_metric_count",
    )), "no intervention, extension, runtime or performance claims")

    for path in ROOT.rglob("*.py"):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except Exception as exc:
            v.errors.append(f"compile failed: {path.name}: {exc}")
    v.require(not any(item.startswith("compile failed") for item in v.errors), "all Python files compile")

    unit = run_command([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-v"])
    ran = re.search(r"Ran (\d+) tests", unit.stderr + unit.stdout)
    unit_count = int(ran.group(1)) if ran else 0
    v.require(unit.returncode == 0 and unit_count >= 16, f"unittest passes ({unit_count} tests)")

    diff_check = run_command(["git", "diff", "--check"])
    v.require(diff_check.returncode == 0, "git diff --check passes")
    status = run_command(["git", "status", "--porcelain", "--untracked-files=all"]).stdout.splitlines()
    outside = [line for line in status if line and "reproduction/instrumentation/l2_h1_on_policy_shadow_instrumentation_v1" not in line]
    v.require(not outside, "all worktree changes remain inside the authorized task-local root")

    secret_patterns = [re.compile(r"ghp_[A-Za-z0-9]{20,}"), re.compile(r"hf_[A-Za-z0-9]{20,}"), re.compile(r"AKIA[0-9A-Z]{16}")]
    secret_hits = []
    large = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.stat().st_size > 1_000_000:
            large.append(path.relative_to(ROOT).as_posix())
        if path.suffix.lower() in {".py", ".json", ".md", ".csv"}:
            text = path.read_text(encoding="utf-8")
            if any(pattern.search(text) for pattern in secret_patterns):
                secret_hits.append(path.relative_to(ROOT).as_posix())
    v.require(not secret_hits, "no credential-like tokens detected")
    v.require(not large, "no unintended large assets")

    status_value = EXPECTED_STATUS if not v.errors else "FAIL_L2_H1_ON_POLICY_SHADOW_INSTRUMENTATION_V1_VALIDATION"
    result = {
        "status": status_value,
        "check_count": len(v.checks),
        "checks": v.checks,
        "errors": v.errors,
        "unittest_count": unit_count,
        "pytest_available": False,
        "pytest_status": "NOT_AVAILABLE_UNITTEST_AND_JSONSCHEMA_COVERAGE_USED",
        "fault_injection_case_count": faults["fault_injection_case_count"],
        "real_navigation_equivalence_run_count": 0,
        "logging_pilot_run_count": 0,
        "formal_on_policy_cohort_count": 0,
        "on_policy_research_collection_count": 0,
        "navigation_rollout_count": 0,
    }
    (ROOT / "validation_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(status_value)
    if v.errors:
        for error in v.errors:
            print(f"ERROR: {error}")
    return 0 if not v.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
