"""Pure semantic rules for Selected Control Actuator Authority V2."""

from __future__ import annotations

from typing import Any


CANONICAL_ACTUATOR = "NORMATIVE_COMPONENTWISE_ACCELERATION_AUTHORITY_V2"


def canonical_scenario() -> dict[str, Any]:
    return {
        "actuator_authority": CANONICAL_ACTUATOR,
        "actuator_authority_resolved": True,
        "backup_actuator_authority": CANONICAL_ACTUATOR,
        "certified_control_id": "candidate-0001",
        "certified_control_vector": [0.01, -0.02, 0.0],
        "desired_mistaken_as_certified": False,
        "executed_control_id": "candidate-0001",
        "executed_control_vector": [0.01, -0.02, 0.0],
        "hidden_delay": False,
        "legacy_controller_path_used": False,
        "physical_actuator_claim": False,
        "physical_actuator_known": False,
        "post_certification_transform": None,
        "rate_limit_authorities": [],
        "selected_control_id": "candidate-0001",
        "selected_control_vector": [0.01, -0.02, 0.0],
        "terminal_actuator_authority": CANONICAL_ACTUATOR,
    }


def validate_scenario(s: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not s.get("actuator_authority_resolved") or s.get("actuator_authority") != CANONICAL_ACTUATOR:
        errors.append("ACTUATOR_AUTHORITY_UNKNOWN_OR_MISMATCH")
    if s.get("post_certification_transform") not in (None, "IDENTITY"):
        errors.append("HIDDEN_POST_CERTIFICATION_TRANSFORM")
    if s.get("selected_control_id") != s.get("executed_control_id") or s.get("selected_control_vector") != s.get("executed_control_vector"):
        errors.append("SELECTED_EXECUTED_MISMATCH")
    if s.get("certified_control_id") != s.get("selected_control_id") or s.get("certified_control_vector") != s.get("selected_control_vector"):
        errors.append("CERTIFICATE_SELECTED_IDENTITY_MISMATCH")
    if s.get("backup_actuator_authority") != CANONICAL_ACTUATOR:
        errors.append("BACKUP_ACTUATOR_AUTHORITY_MISMATCH")
    if s.get("terminal_actuator_authority") != CANONICAL_ACTUATOR:
        errors.append("TERMINAL_ACTUATOR_AUTHORITY_MISMATCH")
    if len(s.get("rate_limit_authorities", [])) > 1:
        errors.append("DUPLICATED_RATE_LIMIT_AUTHORITY")
    if s.get("hidden_delay"):
        errors.append("HIDDEN_ACTUATION_DELAY")
    if s.get("desired_mistaken_as_certified"):
        errors.append("DESIRED_COMMAND_MISTAKEN_AS_CERTIFIED")
    if s.get("legacy_controller_path_used"):
        errors.append("LEGACY_CONTROLLER_PATH_NOT_QUARANTINED")
    if s.get("physical_actuator_claim") and not s.get("physical_actuator_known"):
        errors.append("PHYSICAL_ACTUATOR_AUTHORITY_NOT_ESTABLISHED")
    return errors
