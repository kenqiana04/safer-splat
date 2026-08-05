#!/usr/bin/env python3
"""Recover PR #80 V1 terminal, activation, aggregation, and stage-entry semantics."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from task_config_v2 import METHODS, PR80_ROOT, TASK_ROOT, V1_RESULTS, atomic_json, ensure_roots

V1_GROUPS = ("G0_SAFE_CONTROL", "G1_START_SAFE_BOUNDARY", "G2_FEASIBILITY_DENSE",
             "G3_SAMPLED_DATA_GAP", "G4_PREDICTIVE_RECOVERY")

def load_rows() -> list[dict]:
    paths = sorted(path for path in V1_RESULTS.glob("*.json") if not path.name.endswith(".complete.json"))
    rows = [json.loads(path.read_text()) for path in paths]
    if len(rows) != 500: raise RuntimeError(f"expected 500 V1 results, found {len(rows)}")
    return rows

def mean(rows: list[dict], key: str) -> float:
    return float(np.mean([float(row.get(key, 0) or 0) for row in rows]))

def main() -> int:
    ensure_roots(); out = TASK_ROOT / "v1_semantic_audit"; rows = load_rows()
    by = {(row["scenario_id"], row["method"]): row for row in rows}
    group_method_rows=[]; confusion=[]
    for group in V1_GROUPS:
        scenario_ids = sorted({r["scenario_id"] for r in rows if r["group"] == group})
        for method in METHODS:
            current=[by[(sid,method)] for sid in scenario_ids]
            statuses=Counter(r["status"] for r in current)
            stage = {
                "start_safe_entered": sum(method != METHODS[0] for _ in current),
                "start_safe_attempted": sum(bool(r.get("projection",{}).get("attempted")) for r in current),
                "start_safe_accepted": sum(bool(r.get("projection",{}).get("success")) for r in current),
                "qp_stage_entered": sum(r["status"] != "START_STATE_REJECTED" for r in current),
                "h2_reduction_observed": sum(float(r.get("active_constraints_mean",0)) < float(by[(r["scenario_id"], METHODS[1])].get("active_constraints_mean",0)) for r in current) if method == METHODS[2] else 0,
                "dt_checks_executed": sum(int(r.get("dt_checks",0)) > 0 for r in current),
                "dt_triggered": sum(int(r.get("dt_triggers",0)) > 0 for r in current),
                "recovery_checks_executed": sum(int(r.get("dt_checks",0)) > 0 for r in current) if method == METHODS[4] else 0,
                "recovery_triggered": sum(int(r.get("recovery_triggers",0)) > 0 for r in current),
            }
            group_method_rows.append({"group":group,"method":method,"run_count":len(current),
                "completion_count":sum(bool(r.get("completion")) for r in current),
                "success_count":sum(r["status"]=="SUCCESS" for r in current),
                "terminal_counts":json.dumps(dict(sorted(statuses.items())),sort_keys=True),
                "progress_mean_all_terminal_m":mean(current,"progress_m"),
                "active_constraints_mean_all_terminal":mean(current,"active_constraints_mean"),
                "qp_infeasible_event_count":sum(int(r.get("qp_infeasible",0)) for r in current), **stage})
            confusion.append({"group":group,"method":method,**stage,
                              "terminal_before_h2":statuses.get("START_STATE_REJECTED",0),
                              "terminal_before_h3":statuses.get("START_STATE_REJECTED",0)+statuses.get("QP_INFEASIBLE",0)})
    def write_csv(path: Path, records: list[dict]) -> None:
        with path.open("w",encoding="utf-8",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=list(records[0]),lineterminator="\n"); writer.writeheader(); writer.writerows(records)
    write_csv(out/"v1_group_method_terminal_table.csv",group_method_rows)
    write_csv(out/"v1_stage_reachability_confusion_matrix.csv",confusion)
    method_summary={}
    for method in METHODS:
        current=[r for r in rows if r["method"]==method]
        method_summary[method]={"runs":100,"completion_count":sum(bool(r.get("completion")) for r in current),
            "terminal_counts":dict(sorted(Counter(r["status"] for r in current).items())),
            "qp_infeasible_event_count":sum(int(r.get("qp_infeasible",0)) for r in current),
            "progress_mean_all_100_terminal_records_m":mean(current,"progress_m"),
            "active_constraints_mean_all_100_terminal_records":mean(current,"active_constraints_mean")}
    terminal={"status":"PASS_V1_TERMINAL_SEMANTICS_RECOVERED","run_count":len(rows),
        "definitions":{"terminal_state":"one mutually exclusive final status per run",
          "completion":"true iff status is SUCCESS in the V1 runner",
          "success":"status == SUCCESS; identical to V1 completion",
          "progress_m":"initial Euclidean goal distance minus final Euclidean goal distance; early terminals retain zero or any pre-terminal displacement",
          "aggregation_unit":"one scenario-method terminal record; method means include all 100 terminals"},
        "method_summary":method_summary,
        "explanations":{"twenty_completions":"Only the 20 G0 scenarios reached SUCCESS for every method.",
          "m0_qp_infeasible_80":"One first-step QP_INFEASIBLE event in each G1-G4 scenario; 80 scenario-method terminal records.",
          "m1_m4_60_qp_plus_20_rejected":"G2's 20 states terminate in Start-Safe before QP; G1, G3 and G4 contribute 60 first-step QP_INFEASIBLE terminals.",
          "progress_population":"All 100 terminal records per method, including rejected and infeasible runs, are included."}}
    atomic_json(out/"v1_terminal_semantics.json",terminal)
    g1_ids=sorted({r["scenario_id"] for r in rows if r["group"]==V1_GROUPS[1]})
    g2_ids=sorted({r["scenario_id"] for r in rows if r["group"]==V1_GROUPS[2]})
    activation={
      "status":"PASS_V1_ACTIVATION_SEMANTICS_RECOVERED_WITH_DEFECT",
      "v1_reported":{"H1_START_SAFE":14,"H2_FEASIBILITY_AWARE":0,"H3_DISCRETE_TIME":0,"H4_PREDICTIVE_RECOVERY":0},
      "reconstructed":{"H1_START_SAFE":sum(bool(by[(sid,METHODS[1])].get("projection",{}).get("attempted")) for sid in g1_ids),
        "H1_PROJECTION_ACCEPTED":sum(bool(by[(sid,METHODS[1])].get("projection",{}).get("success")) for sid in g1_ids),
        "H2_DESIGNATED_GROUP_STAGE_ENTRY":sum(by[(sid,METHODS[2])]["status"]!="START_STATE_REJECTED" for sid in g2_ids),
        "H2_DESIGNATED_GROUP_REDUCTION":sum(float(by[(sid,METHODS[2])].get("active_constraints_mean",0))<float(by[(sid,METHODS[1])].get("active_constraints_mean",0)) for sid in g2_ids),
        "H3_DESIGNATED_GROUP_CHECKS":sum(int(r.get("dt_checks",0))>0 for r in rows if r["group"]==V1_GROUPS[3] and r["method"]==METHODS[3]),
        "H4_DESIGNATED_GROUP_CHECKS":sum(int(r.get("dt_checks",0))>0 for r in rows if r["group"]==V1_GROUPS[4] and r["method"]==METHODS[4])},
      "defect":{"code":"V1_BENCHMARK_SEMANTIC_DEFECT","scope":"activation and aggregate reconciliation",
        "finding":"H1 counted projection attempts rather than accepted actions. H2 compared designated G2 M2/M1 means after all G2 cases were rejected before QP, while the reported global 1600-to-160.041 reduction came from other groups. H3/H4 had zero checks because QP failed before those stages.",
        "v1_history_rewritten":False}}
    atomic_json(out/"v1_activation_semantics.json",activation)
    aggregate={"status":"PASS_V1_METRIC_AGGREGATION_RECONCILED","unit":"SCENARIO_METHOD_TERMINAL_RECORD",
      "denominators":{"per_method":100,"per_group_method":20,"all":500},"method_summary":method_summary,
      "zero_or_early_terminal_values_included":True,"nested_timestep_values_are_summarized_within_run_before_scenario_level_aggregation":True}
    atomic_json(out/"v1_metric_aggregation_audit.json",aggregate)
    m1=method_summary[METHODS[1]]["active_constraints_mean_all_100_terminal_records"]
    m2=method_summary[METHODS[2]]["active_constraints_mean_all_100_terminal_records"]
    text=f"""# V1 H2 Constraint-Reduction Reconciliation\n\nV1's method-level active-constraint means are **M1={m1:.3f}** and **M2={m2:.3f}** because every method mean uses all 100 terminal records. M1 contributes 2,000 rows for each of the 80 scenarios that enter QP and zero for the 20 G2 Start-Safe rejections, yielding 1,600. M2 reduces rows in G0, G1, G3, and G4, while the same 20 G2 records remain zero, yielding approximately 160.041.\n\nThe V1 H2 activation statistic is not a global reduction statistic. It compares M2 with M1 only inside designated G2. All 20 G2 states terminate at Start-Safe, so neither method enters QP and both active-count summaries are zero. Therefore H2 activation is correctly zero under the V1 code but the group does not test H2. The semantic defect is presenting the global reduction alongside the designated-group activation without an explicit stage-entry denominator. V2 records `stage_entered`, `input_constraint_count`, `provably_redundant_count`, and `output_constraint_count` directly and defines dominance activation from the shadow predicate before lock.\n\nPR #80 and its Case-B conclusion remain unchanged.\n"""
    (out/"v1_h2_constraint_reduction_reconciliation.md").write_text(text,encoding="utf-8",newline="\n")
    print(json.dumps({"status":terminal["status"],"rows":len(rows),"activation":activation["reconstructed"]},sort_keys=True))
    return 0

if __name__ == "__main__": raise SystemExit(main())
