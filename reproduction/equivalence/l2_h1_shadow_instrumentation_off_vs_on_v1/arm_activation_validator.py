#!/usr/bin/env python3
"""Validate arm activation evidence without conflating health with control."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(record: dict) -> tuple[bool, list[str]]:
    arm = record["arm"]
    checks: list[tuple[bool, str]] = []
    checks.append((record.get("controller_authority") is False, "controller authority is false"))
    checks.append((record.get("controller_intervention_count") == 0, "zero intervention"))
    checks.append((record.get("selected_candidate_replacement_count") == 0, "zero candidate replacement"))
    checks.append((record.get("leftover_shadow_worker_count") == 0, "no leftover worker"))
    if arm == "NATIVE_OFF":
        checks.extend([
            (record.get("wrapper_loaded") is False, "wrapper absent"),
            (record.get("worker_ident_after_start") is None, "worker not started"),
            (record.get("capture_log_count") == 0 and record.get("certificate_result_count") == 0, "no observer logs"),
        ])
    elif arm == "WRAPPER_OFF":
        checks.extend([
            (record.get("wrapper_loaded") is True and record.get("wrapper_factory_trial_count") == 1, "wrapper delegated one frozen CBF instance"),
            (record.get("observer_enabled") is False and record.get("worker_ident_after_start") is None, "observer and worker disabled"),
            (record.get("certificate_result_count") == 0, "no certificate result"),
        ])
    elif arm == "WRAPPER_ON":
        checks.extend([
            (record.get("wrapper_loaded") is True and record.get("wrapper_factory_trial_count") == 1, "wrapper delegated one frozen CBF instance"),
            (record.get("observer_enabled") is True and record.get("worker_ident_after_start") is not None, "observer and worker started"),
            (record.get("capture_log_count", 0) > 0 and record.get("certificate_result_count", 0) > 0, "valid capture and certificate observations"),
            (record.get("worker_processed_count", 0) > 0, "worker processed observations"),
            (record.get("worker_alive_after_shutdown") is False, "worker cleanly absent after run"),
        ])
    else:
        checks.append((False, "known arm"))
    failures = [label for passed, label in checks if not passed]
    return not failures and record.get("intended_state_valid") is True, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    passed, failures = validate(record)
    print(json.dumps({"status": "PASS_ARM_ACTIVATION" if passed else "FAIL_ARM_ACTIVATION", "failures": failures}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
