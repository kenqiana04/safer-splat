"""Candidate-pool entrypoint guarded by the frozen method-fairness gate."""
import json
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    audit = json.loads((TASK_ROOT / "methods/fairness_audit.json").read_text(encoding="utf-8"))
    if not audit["fairness_pass"]:
        raise SystemExit("METHOD_FAIRNESS_GATE_NOT_PASS_CANDIDATE_GENERATION_FORBIDDEN")
    raise SystemExit("UNREACHABLE_WITH_CURRENT_FROZEN_PR84_IDENTITY")


if __name__ == "__main__":
    main()
