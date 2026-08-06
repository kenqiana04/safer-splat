import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_frozen_inputs_pass():
    assert load("input_freeze/pr84_identity.json")["status"] == "PASS_PR84_AND_EXTERNAL_INPUT_FREEZE"
    assert load("input_freeze/replica_map_identity.json")["status"] == "PASS_REPLICA_GT_FINE_IDENTITY"
    assert load("input_freeze/reference_mesh_identity.json")["status"] == "PASS_OFFICIAL_REPLICA_REFERENCE_IDENTITY"


def test_method_fairness_blocks_before_search():
    audit = load("methods/fairness_audit.json")
    assert audit["status"] == "BLOCKED_BY_METHOD_FAIRNESS_CONTRACT_MISMATCH"
    assert audit["candidate_search_started"] is False
    assert audit["formal_benchmark_started"] is False


def test_missing_library_identity_is_explicit():
    facts = load("methods/fairness_audit.json")["facts"]
    assert facts["alternative_controls_is_caller_supplied"] is True
    assert facts["candidate_library_control_constructor_count"] == 0
    assert facts["alternative_library_size_frozen"] is False
    assert facts["alternative_library_canonical_identity_frozen"] is False


def test_zero_execution_boundary():
    counters = load("audits/execution_count_audit.json")["counters"]
    for key in ("candidate_generation_count", "physical_valid_count", "stage_predicate_evaluation_count", "registry_state_count", "prelock_future_reference_read_count", "prelock_formal_rollout_count", "reference_online_read_count", "one_step_method_run_count", "logical_episode_count", "logical_control_step_count", "formal_attempt_count"):
        assert counters[key] == 0


def test_no_registry_lock_or_reference_query():
    assert load("registry/registry_lock.json")["status"] == "NOT_LOCKED_BLOCKED_BEFORE_REGISTRY"
    assert load("reference/reference_oracle_access_log.json")["events"] == []


def test_claim_boundary():
    audit = load("audits/claim_boundary_audit.json")
    assert audit["fail_closed_not_safe_stop"] is True
    assert audit["candidate_exhaustion_not_unrecoverable"] is True
    assert audit["forbidden_claims_made"] == []
