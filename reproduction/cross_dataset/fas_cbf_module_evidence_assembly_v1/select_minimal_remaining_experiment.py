#!/usr/bin/env python3
"""Select the protocol decision without authorizing a new experiment."""
from __future__ import annotations

from evidence_common import TASK, write_json


def main() -> int:
    decision = {
        "FINAL_STATUS": "PASS_MODULE_WISE_EVIDENCE_WITHOUT_FULL_STACK_SUPERIORITY",
        "FINAL_DECISION": "FRAME_PAPER_AS_MODULAR_SAFETY_ASSURANCE_NOT_GLOBAL_SUPERIORITY",
        "ONLY_NEXT_TASK": "INTEGRATE_FAS_CBF_FULL_FRAMEWORK_WITH_MODULE_SPECIFIC_CLAIMS_V1",
        "case": "B",
        "new_experiment_authorized": False,
        "minimal_remaining_experiment": "No new experiment is required for the module-wise paper framing. A future global-superiority claim would require separately authorized one-map, outcome-blind, fully activated paired evidence; this task neither authorizes nor schedules it.",
        "reason": "Start-Safe has active support, constraint/efficiency has formal support, DT has detection/precursor evidence, and recovery has active configuration-specific support, but no same-map activated full-stack paired superiority evidence exists."
    }
    write_json(TASK / "minimal_remaining_experiment/minimal_remaining_experiment.json", decision)
    print("PASS_MINIMAL_REMAINING_EXPERIMENT_DECISION case=B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
