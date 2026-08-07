"""Run the frozen PR87 runtime against the unchanged 160-state registry."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

CURRENT_ROOT = Path(__file__).resolve().parents[1]
PRIOR_ROOT = Path("/disk1/zlab/maintenance_records/resume_replica_gt_executable_safety_activated_benchmark_v1")
sys.path.insert(0, str(PRIOR_ROOT))
from runtime_core import ReplicaRuntime  # noqa: E402
from task_config import MAP_ROOT, METHODS, SLOT_IDS  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--mode", choices=("smoke", "formal"), required=True); args = parser.parse_args()
    registry = json.loads((PRIOR_ROOT / "registry/representative_holdout_registry_v1.json").read_text(encoding="utf-8"))
    states = registry["states"][:8] if args.mode == "smoke" else registry["states"]
    runtime = ReplicaRuntime(Path(MAP_ROOT)); records = []
    for state in states:
        decisions = [runtime.method_decision(method, state) for method in METHODS]
        b0, b1, b2, b3 = decisions
        segment = bool(b0["committed"] and not b1["committed"] and b1["semantic_status"] == "FAIL_CLOSED_IMMEDIATE_SEGMENT_UNSAFE")
        backup = bool(b1["committed"] and not b2["committed"] and "BACKUP" in str(b2["typed_reason"]))
        directional = bool(not b2["committed"] and b3["committed"] and b3["selected_candidate"] in SLOT_IDS)
        for decision in decisions:
            decision.update({"environment": "E1_REPLICA_GT_FINE", "reference_tier": "TIER_R3_REFERENCE_COMPLETE", "registry_sha256": "eaa0f9f63cbcae433741b959441cf244648e30bf184b62309334602b76659a1a", "formal_attempt": args.mode == "formal", "segment_incremental_activation": segment, "backup_incremental_activation": backup, "directional_incremental_rescue": directional, "any_incremental_activation": segment or backup or directional, "terminal_already_safe": decision["semantic_status"] == "CERTIFIED_TERMINAL_ACTION"})
            records.append(decision)
    target = CURRENT_ROOT / ("runtime_work/smoke" if args.mode == "smoke" else "runtime_work/formal") / "E1_REPLICA_GT_FINE.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    fields = []
    for record in records:
        for key in record:
            if key not in fields: fields.append(key)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fields, lineterminator="\n"); writer.writeheader()
        for record in records:
            writer.writerow({key: json.dumps(value, separators=(",", ":")) if isinstance(value, (dict, list)) else value for key, value in record.items()})
    target.with_suffix(".json").write_text(json.dumps({"environment": "E1_REPLICA_GT_FINE", "mode": args.mode, "state_count": len(states), "method_record_count": len(records), "status": "PASS_" + args.mode.upper() + "_ONE_STEP"}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("PASS E1_REPLICA_GT_FINE", args.mode, len(states), len(records))


if __name__ == "__main__": main()
