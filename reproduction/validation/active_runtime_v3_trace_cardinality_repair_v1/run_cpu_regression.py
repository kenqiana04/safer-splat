#!/usr/bin/env python3
"""Run behavior regressions while excluding one superseded upstream blob-lock assertion."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


EXCLUDED = {
    "test_existing_runtime_regression.ExistingRuntimeRegressionTests.test_still_protected_runtime_blobs_match_input_lock",
}


def cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from cases(item)
        else:
            yield item


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    loader = unittest.TestLoader()
    discovered = unittest.TestSuite()
    for relative in (
        "reproduction/runtime/active_runtime_assurance_v2/tests",
        "reproduction/validation/v3_hard_radius_runtime_wiring_v1/tests",
        "reproduction/validation/active_runtime_v3_trace_cardinality_repair_v1/tests",
    ):
        discovered.addTests(loader.discover(str(root / relative), top_level_dir=str(root)))

    selected = unittest.TestSuite()
    excluded = []
    for case in cases(discovered):
        short_id = case.id().split("reproduction.runtime.active_runtime_assurance_v2.tests.")[-1]
        if short_id in EXCLUDED:
            excluded.append(case.id())
        else:
            selected.addTest(case)

    result = unittest.TextTestRunner(verbosity=1).run(selected)
    payload = {
        "schema": "ACTIVE_RUNTIME_V3_TRACE_CARDINALITY_CPU_REGRESSION_V1",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "excluded_superseded_identity_assertions": excluded,
        "excluded_reason": "The upstream test freezes active_cycle.py and supervisor.py blobs that this narrowly authorized repair must change; exact change scope is validated separately.",
        "status": "PASS" if result.wasSuccessful() and excluded == [
            "reproduction.runtime.active_runtime_assurance_v2.tests.test_existing_runtime_regression.ExistingRuntimeRegressionTests.test_still_protected_runtime_blobs_match_input_lock"
        ] else "FAIL",
    }
    output = Path(__file__).resolve().parent / "CPU_REGRESSION_RESULT.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
