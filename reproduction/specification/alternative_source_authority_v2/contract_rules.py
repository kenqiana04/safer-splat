"""Pure static rules for Alternative Source Authority V2."""

IDENTITY_FIELDS = (
    "candidate_id",
    "source_type",
    "creation_timestamp",
    "state_identity",
    "map_identity",
    "actuator_authority",
    "controller_identity",
)
AUTHORIZED_SOURCE = "SOURCE_NATIVE_EXISTING"
FORBIDDEN_GENERATION = {
    "RANDOM_PERTURBATION",
    "NOISE_INJECTION",
    "INTERPOLATION",
    "HEURISTIC_STEERING",
    "OUTCOME_CONDITIONED_GENERATION",
    "COLLISION_DRIVEN_CANDIDATE_CREATION",
}


def validate_contract(contract: dict, taxonomy: dict, chain: dict) -> list[str]:
    errors: list[str] = []
    if contract.get("search_authority_owner") != "SUPERVISOR" or contract.get("search_authority_owner_count") != 1:
        errors.append("ALTERNATIVE_SEARCH_OWNER_NOT_UNIQUE_SUPERVISOR")
    l4 = contract.get("l4_role", {})
    if not l4.get("may_request_alternative_evaluation") or any(l4.get(k) for k in ("may_create_candidate", "may_select_candidate", "may_commit_candidate")):
        errors.append("L4_AUTHORITY_EXCEEDS_REQUEST_ONLY")
    if contract.get("default_authorized_sources") != [AUTHORIZED_SOURCE] or taxonomy.get("authorized_source_set_v2") != [AUTHORIZED_SOURCE]:
        errors.append("DEFAULT_SOURCE_SET_INVALID")
    synthetic = taxonomy.get("sources", {}).get("SOURCE_SYNTHETIC", {})
    if synthetic.get("authorized_by_default") or not synthetic.get("forbidden_in_this_contract"):
        errors.append("SYNTHETIC_SOURCE_NOT_FORBIDDEN")
    if not FORBIDDEN_GENERATION.issubset(set(taxonomy.get("prohibited_generation_methods", []))):
        errors.append("OUTCOME_OR_SYNTHETIC_GENERATION_NOT_FULLY_FORBIDDEN")
    if contract.get("mandatory_recertification_chain") != ["C0", "L1", "L2", "L3"]:
        errors.append("RECERTIFICATION_CHAIN_INCOMPLETE")
    if contract.get("previous_certificate_reuse_allowed") is not False or chain.get("previous_certificate_reuse_allowed") is not False:
        errors.append("CERTIFICATE_REUSE_ALLOWED")
    if [x.get("stage") for x in chain.get("chain", [])] != ["C0", "L1", "L2", "L3"] or not all(x.get("fresh_result_required") for x in chain.get("chain", [])):
        errors.append("FRESH_RECERTIFICATION_NOT_MANDATORY")
    gate = contract.get("deadline_gate", {})
    if gate.get("DEADLINE_OPEN") != "ALTERNATIVE_EVALUATION_MAY_BE_REQUESTED" or "NO_NEW" not in gate.get("DEADLINE_WARNING", "") or gate.get("DEADLINE_EXPIRED") != "ALTERNATIVE_SEARCH_FORBIDDEN":
        errors.append("DEADLINE_COMPATIBILITY_INVALID")
    return errors


def candidate_provenance_errors(candidate: dict) -> list[str]:
    errors = [f"MISSING_{field.upper()}" for field in IDENTITY_FIELDS if field not in candidate or candidate[field] in (None, "")]
    if candidate.get("source_type") != AUTHORIZED_SOURCE:
        errors.append("SOURCE_NOT_AUTHORIZED")
    if candidate.get("actuator_authority") != "NORMATIVE_COMPONENTWISE_ACCELERATION_AUTHORITY_V2":
        errors.append("ACTUATOR_AUTHORITY_MISMATCH")
    if candidate.get("existed_before_alternative_request") is not True:
        errors.append("NOT_NATIVE_EXISTING_BEFORE_REQUEST")
    return errors


def identity_update_is_valid(old: dict, new: dict) -> bool:
    changed_non_id = any(old.get(field) != new.get(field) for field in IDENTITY_FIELDS if field != "candidate_id")
    if changed_non_id and old.get("candidate_id") == new.get("candidate_id"):
        return False
    return True


def request_allowed(deadline_state: str) -> bool:
    return deadline_state == "DEADLINE_OPEN"


def backup_dual_role_compatible(record: dict) -> bool:
    required_true = ("geometry_identity_match", "actuator_authority_match", "map_authority_match", "state_identity_match", "fresh_c0_l1_l2_l3")
    return all(record.get(field) is True for field in required_true) and record.get("source_type") == AUTHORIZED_SOURCE


def ordinary_success_allowed(status: str) -> bool:
    return status not in {"NO_ALTERNATIVE_AVAILABLE", "SOURCE_INVALID", "PROVENANCE_MISSING", "ALTERNATIVE_CERTIFICATION_FAILED", "ALTERNATIVE_SEARCH_BLOCKED_BY_DEADLINE", "UNKNOWN_SOURCE"}
