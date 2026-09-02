"""Pure, task-local static rules for the V2 deadline-authority specification."""

LEGAL_EXPIRED = {
    "ALREADY_CERTIFIED_NAVIGATION_ACTION",
    "ALREADY_VALID_BACKUP_WITNESS",
    "ALREADY_CERTIFIED_TERMINAL_ACTION",
    "OUTSIDE_METHOD_BOUNDARY",
}


def validate_contract(contract: dict) -> list[str]:
    errors: list[str] = []
    if contract.get("authority_owner") != "SUPERVISOR" or contract.get("authority_owner_count") != 1:
        errors.append("GLOBAL_DEADLINE_OWNER_NOT_UNIQUE_SUPERVISOR")
    layer_owners = contract.get("certificate_layer_deadline_owners", {})
    if any(layer_owners.values()):
        errors.append("CERTIFICATE_LAYER_CLAIMS_GLOBAL_DEADLINE")
    expired = contract.get("states", {}).get("DEADLINE_EXPIRED", {})
    if expired.get("continue_search") or expired.get("start_any_new_search"):
        errors.append("SEARCH_AFTER_EXPIRY")
    warning = contract.get("states", {}).get("DEADLINE_WARNING", {})
    if warning.get("start_high_cost_search"):
        errors.append("HIGH_COST_SEARCH_AFTER_WARNING")
    if set(contract.get("post_expiry_legal_choices", [])) != LEGAL_EXPIRED:
        errors.append("POST_EXPIRY_CHOICE_SET_INVALID")
    forbidden = set(contract.get("post_expiry_forbidden_choices", []))
    if not {"NOMINAL_CONTROL", "DESIRED_CONTROL", "UNCERTIFIED_CANDIDATE"}.issubset(forbidden):
        errors.append("UNCERTIFIED_FALLBACK_NOT_FORBIDDEN")
    unknown = contract.get("unknown_semantics", {})
    if unknown.get("ordinary_success_allowed") is not False:
        errors.append("UNKNOWN_OR_TIMEOUT_CAN_ENTER_SUCCESS")
    if contract.get("clock_contract", {}).get("numeric_defaults_authorized") is not False:
        errors.append("IMPLICIT_NUMERIC_DEFAULT_AUTHORIZED")
    return errors


def backup_is_valid(record: dict) -> bool:
    required = ("geometry_identity_match", "actuator_authority_match", "state_identity_match", "map_authority_match", "temporal_validity", "completed_before_expiry")
    return all(record.get(key) is True for key in required)


def terminal_is_executable(record: dict) -> bool:
    return record.get("status") == "CERTIFIED_TERMINAL_READY" and record.get("completed_before_expiry") is True


def ordinary_success_allowed(status: str) -> bool:
    return status not in {"GLOBAL_DEADLINE_UNKNOWN", "LOCAL_CERTIFICATE_TIMEOUT", "DEADLINE_EXPIRED"}
