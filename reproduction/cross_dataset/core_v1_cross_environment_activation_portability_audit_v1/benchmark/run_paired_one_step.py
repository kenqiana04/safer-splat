"""Smoke/formal runner for frozen representative registries."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common import read_json, write_csv, write_json  # noqa: E402
from task_config import METHODS  # noqa: E402
from source_runtime import SourceRuntime  # noqa: E402

SCENES = {
    "E5_STONEHENGE_SAFER": ("/disk1/zlab/projects/safer-splat/outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml", "ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d"),
    "E6_FLIGHT_SAFER": ("/disk1/zlab/projects/safer-splat/outputs/flight/splatfacto/2024-09-12_172434/config.yml", "8e7499a0d68405065b0effb7022b635ef3fbe50a53b69f5f25165260c8a493e6"),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", choices=SCENES, required=True)
    parser.add_argument("--mode", choices=("smoke", "formal"), required=True)
    args = parser.parse_args()
    registry = read_json(ROOT / "registry" / args.environment / "representative_registry.json")
    states = registry["states"][:8] if args.mode == "smoke" else registry["states"]
    runtime = SourceRuntime(Path(SCENES[args.environment][0]), SCENES[args.environment][1])
    records = []
    for state in states:
        decisions = []
        for method in METHODS:
            decision = runtime.method_decision(method, state)
            decision.update({"environment": args.environment, "reference_tier": "TIER_R1_REPRESENTED_MAP_BEHAVIOR_ONLY", "registry_sha256": read_json(ROOT / "registry" / args.environment / "registry_identity.json")["registry_sha256"], "formal_attempt": args.mode == "formal", "offline_reference_collision": "NOT_EVALUABLE", "map_reference_disagreement": "NOT_EVALUABLE"})
            decisions.append(decision)
        b0, b1, b2, b3 = decisions
        segment = bool(b0["committed"] and not b1["committed"] and b1["semantic_status"] == "FAIL_CLOSED_IMMEDIATE_SEGMENT_UNSAFE")
        # A pre-existing zero-velocity terminal state is reported separately and
        # is never promoted to incremental backup activation.
        backup = bool(b1["committed"] and not b2["committed"] and "BACKUP" in str(b2["typed_reason"]))
        directional = bool(not b2["committed"] and b3["committed"] and b3["selected_candidate"] in {"ALT-01-OUTWARD", "ALT-02-GOAL-TANGENT", "ALT-03-AUX-TANGENT-POS", "ALT-04-AUX-TANGENT-NEG", "ALT-05-BRAKE-BIASED-GOAL-TANGENT", "ALT-06-BRAKE-BIASED-OUTWARD"})
        for decision in decisions:
            decision.update({"segment_incremental_activation": segment, "backup_incremental_activation": backup, "directional_incremental_rescue": directional, "any_incremental_activation": segment or backup or directional, "terminal_already_safe": decision["semantic_status"] == "CERTIFIED_TERMINAL_ACTION", "represented_false_safe": False, "reference_safe_but_rejected": "NOT_EVALUABLE"})
            records.append(decision)
    target = ROOT / ("runtime_work/smoke" if args.mode == "smoke" else "runtime_work/formal") / f"{args.environment}.csv"
    write_csv(target, records)
    write_json(target.with_suffix(".json"), {"environment": args.environment, "mode": args.mode, "state_count": len(states), "method_record_count": len(records), "status": "PASS_" + args.mode.upper() + "_ONE_STEP"})
    print("PASS", args.environment, args.mode, len(states), len(records))


if __name__ == "__main__":
    main()
