"""Build the compact, evidence-bounded Protocol V2 technical report."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from requalification_core import MAP_ORDER, ROOT


REPORT = ROOT / "REPORT_RETROSPECTIVE_REQUALIFY_EXISTING_GAUSSIAN_MAPS_UNDER_LAYERED_PROTOCOL_V2.md"


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def truth(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def main() -> None:
    freeze = load("input_freeze/protocol_v2_input_freeze.json")
    inventory = load("map_inventory/requalification_map_inventory.json")
    controls = load("control_validation/protocol_v2_control_discrimination.json")
    positive = load("control_validation/positive_control_result.json")
    negative = load("control_validation/negative_control_result.json")
    matrix = load("classification/classification_matrix.json")["maps"]
    claims = load("classification/allowed_forbidden_claims.json")["maps"]
    parity = load("native_common/native_common_parity_per_map.json")["maps"]
    risk = load("risk_coverage/risk_coverage_per_map.json")["maps"]
    multi = load("multi_tolerance/multi_tolerance_per_map.json")["maps"]
    unknown = load("unknown/unknown_missingness_per_map.json")["maps"]
    routes = load("route_tube/replica_route_tube_per_map.json")["maps"]
    one_sided = load("route_tube/one_sided_route_risk_per_map.json")["maps"]
    budget = load("physical_budget/physical_budget_per_map.json")["maps"]
    g0 = load("safer_g0/safer_g0_summary.json")["maps"]
    decision = load("classification/final_decision.json")
    manifest = load("run_manifest.json")

    by_id = {row["map_id"]: row for row in matrix}
    inv_by_id = {row["map_id"]: row for row in inventory["maps"]}
    claim_by_id = {row["map_id"]: row for row in claims}
    parity_counts = Counter(row["status"] for row in parity)

    lines: list[str] = []
    add = lines.append
    add("# REPORT: Retrospective Requalification of Existing Gaussian Maps under Layered Protocol V2")
    add("")
    add("## Executive result")
    add("")
    add(f"**{decision['FINAL_STATUS']}**")
    add("")
    add(f"Frozen decision-tree outcome: **{decision['FINAL_DECISION']}**. The only next task is **{decision['Only_next_task']}**, which authorizes entry qualification only—not ETH3D download or training.")
    add("")
    add("Protocol V2 correctly discriminated the controls. The GT-derived positive control reached R3/N3, while the executable learned negative control remained R1/N1 despite finite G0 queries. No learned map reached N2 or N3. Six existing artifacts were inspected read-only; five unavailable artifacts were retained as unavailable rather than reconstructed.")
    add("")
    add("## Frozen identities and scope")
    add("")
    add(f"- Upstream PR/head: #75 at `{freeze['upstream_head']}`; base branch `{freeze['upstream_branch']}`.")
    add(f"- Protocol V2 SHA-256: `{freeze['observed']['protocol_v2_sha256']}`.")
    add(f"- New-dataset checklist SHA-256: `{freeze['observed']['checklist_sha256']}`.")
    add(f"- PR #75 report SHA-256: `{freeze['observed']['upstream_report_sha256']}`.")
    add("- Identity method: raw Git blob bytes from the frozen upstream head; working-tree EOL conversion is excluded.")
    add("- This task performed no download, training, optimization, resume, map mutation, filtering, registration, scale repair, frame deletion, controller run, planner run, or route generation.")
    add("- For every entry, the legacy result remains valid under legacy contract. Historical PR #68–#75 conclusions remain valid under their original contracts. V2 supplies a new task-specific classification and does not rewrite history.")
    add("")
    add("## Map inventory and Protocol V2 classification")
    add("")
    add(f"Inventory: {inventory['map_count']} fixed entries; {inventory['accessible_count']} accessible and {inventory['unavailable_count']} unavailable for retrospective execution.")
    add("")
    add("| Map | Artifact | Learned | R axis | N axis | Query | Reference | Unknown | Physical budget |")
    add("|---|---:|---:|---|---|---|---|---|---|")
    for map_id in MAP_ORDER:
        row = by_id[map_id]
        inv = inv_by_id[map_id]
        add(f"| {map_id} | {'available' if inv['available'] else 'unavailable'} | {truth(row['learned'])} | {row['V2_RECONSTRUCTION_AXIS']} | {row['V2_NAVIGATION_AXIS']} | {truth(row['SAFETY_QUERY_COMPATIBLE'])} | {row['REFERENCE_AUTHORITY']} | {row['UNKNOWN_MODEL_STATUS']} | {row['PHYSICAL_BUDGET_STATUS']} |")
    add("")
    add("The GT-derived map is a control, not a learned-map success. `SAFETY_QUERY_COMPATIBLE=true` is reported independently and never raises either axis.")
    add("")
    add("## Control-first gate")
    add("")
    add(f"Control discrimination: **{controls['status']}**. Positive control: {positive['R']}/{positive['N']}, query={truth(positive['SAFETY_QUERY_COMPATIBLE'])}, frozen route/oracle closure retained. Negative control: {negative['R']}/{negative['N']}, query={truth(negative['SAFETY_QUERY_COMPATIBLE'])}; finite G0 did not create a navigation qualification. TUM Splatfacto remains historical negative evidence because its artifact is unavailable.")
    add("")
    add("The initial generic GT G0 wrapper mishandled inactive uniform-sphere entries and a subsequent retry called the CUDA peak-memory reset before CUDA initialization. Both wrapper-only failures are preserved. The wrapper was corrected without modifying map bytes or the SAFER solver, then all three required fresh GT processes passed deterministically.")
    add("")
    add("## Evidence channels")
    add("")
    add(f"Native/common parity counts: `{dict(sorted(parity_counts.items()))}`. TUM SplaTAM and TUM Gaussian-SLAM have numeric parity; three maps have semantic parity only; ARKit M1 is native-only; five artifacts are not evaluable. Renderer selection was not changed to favor a candidate.")
    add("")
    add("Risk–coverage uses the frozen 11-point alpha grid. ARKit M1 reuses one complete frozen curve and its historical alpha=0.5 point; Replica learned maps have only retained single working points; TUM entries have historical single geometry evidence. No interpolation, candidate-specific alpha, rerender, or hard AURC gate was introduced.")
    add("")
    add("Multi-tolerance reporting uses 0.01/0.02/0.03/0.05/0.10/0.20 m. Only the GT-derived deterministic construction certificate is complete; no learned map has retained bidirectional samples sufficient for a full new multi-tolerance curve. Authority-B claims remain observable-ray bounded and are not called full-space completeness.")
    add("")
    add("UNKNOWN is never treated as FREE. ARKit M1 supports diagnostic missingness only; ten other entries are unresolved or not applicable to the GT-derived full-reference control. Diagnostic rejected-pixel or observable-ray masks are not represented as a deployable runtime unknown model.")
    add("")
    add("Only the GT-derived Replica control has a frozen route-coordinate contract, 100-route registry, swept-body oracle, one-sided deterministic certificate, and resolved physical budget. Replica learned maps do not have a proven coordinate identity to that route registry. No candidate-dependent route was generated. The exact one-sided engine was independently checked on 256 frozen queries with chunked full-map evaluation; empirical-only evidence is not promoted to N3.")
    add("")
    add("## Read-only SAFER G0")
    add("")
    add("Six accessible maps ran 256 fixed queries in three fresh processes each (18 total) on physical GPU 1. Every final process produced finite h/gradient/Hessian values, symmetric Hessians, deterministic active indices and unchanged source identity. The source was the corrected world-frame Hessian implementation at commit `f63b4c496861c4f8881348d74244c1ff9a528d51`. G0 establishes query compatibility only.")
    add("")
    add("| Map | Processes | Max runtime (s) | Max peak GPU bytes | Result |")
    add("|---|---:|---:|---:|---|")
    for row in g0:
        if row["status"] == "PASS_SAFETY_QUERY_COMPATIBILITY":
            add(f"| {row['map_id']} | {row['run_count']} | {max(row['runtime_s']):.6f} | {max(row['peak_gpu_bytes'])} | PASS |")
        else:
            add(f"| {row['map_id']} | 0 | — | — | NOT_EVALUABLE |")
    add("")
    add("## Candidate-specific conclusions")
    add("")
    add("- **Replica SplaTAM 60:** the legacy delta1=0.743966766 threshold failure remains valid and is marked `LEGACY_SINGLE_THRESHOLD_BORDERLINE`. V2 does not establish that it was “mis-killed”: only a single working point survives; unknown semantics, route-coordinate proof, route-tube evidence, and physical budget remain unresolved. Result R1/N1/query-compatible.")
    add("- **ARKitScenes M1 SplaTAM:** the legacy formal failure remains valid. The frozen 11-point curve supports R2 reconstruction-candidate evidence and diagnostic missingness, but no legal route/robot contract/runtime unknown/physical budget supports navigation. Result R2/N0/query-compatible; limited navigation is not evaluable.")
    add("- **TUM SplaTAM:** geometry/query evidence is separated from historical navigation progress failure. Numeric native/common parity and G0 do not supply independent full-scene reference, route, robot, unknown, or budget closure. Result R1/N0/query-compatible.")
    add("- **TUM Gaussian-SLAM:** adapter semantics, numeric parity, far-range historical geometry, and G0 are recorded independently from navigation. Missing route/reference/unknown/budget closure caps it at R1/N0/query-compatible.")
    add("")
    add("## Allowed and forbidden claims")
    add("")
    for map_id in MAP_ORDER:
        row = claim_by_id[map_id]
        add(f"### {map_id}")
        add("")
        add("Allowed: " + "; ".join(row["allowed"]) + ".")
        add("")
        add("Forbidden: " + "; ".join(row["forbidden"]) + ".")
        add("")
    add("## Required 29-answer audit")
    add("")
    answers = [
        f"Protocol V2 identity is byte-exact: `{freeze['observed']['protocol_v2_sha256']}`.",
        "PR #75 is the immutable upstream lineage; PR #68–#75 were not modified, and this report is a new V2 task classification.",
        f"The fixed inventory contains 11 maps: {inventory['accessible_count']} accessible and {inventory['unavailable_count']} unavailable.",
        f"The controls passed: `{controls['status']}`.",
        "The positive control REPLICA_GT_FINE is R3/N3/query-compatible with frozen route, oracle, one-sided certificate and resolved budget.",
        "REPLICA_SPLATFACTO remains R1/N1 despite query compatibility; TUM_SPLATFACTO_NEGATIVE remains historical negative evidence and is not executable.",
        f"Native/common status counts are {dict(sorted(parity_counts.items()))}.",
        "One complete frozen risk–coverage curve exists (ARKit M1); other learned evidence is single-point or unavailable.",
        "One deterministic GT multi-tolerance certificate exists; no learned map has a complete new multi-tolerance evaluation.",
        "One ARKit diagnostic missingness record is complete; no learned deployable runtime unknown model is established.",
        "Only the GT control has a closed route-coordinate contract.",
        "Only the GT control has a complete frozen route-tube evaluation.",
        "Only the GT control has deterministic one-sided route-risk closure.",
        "One physical budget is resolved and ten are unresolved.",
        "Six maps completed G0 in 18 fresh processes; G0 affects query compatibility only.",
        "Per-map R axes are listed in the classification table.",
        "Per-map N axes are listed in the classification table.",
        "Per-map query compatibility is listed independently in the classification table.",
        "Per-map allowed and forbidden claims are listed above and serialized in the evidence cards.",
        "Replica SplaTAM is not proven retrospectively qualified; its borderline legacy single threshold is not overturned.",
        "ARKit M1 limited navigation is not evaluable under V2 because route, robot, runtime unknown and budget evidence are absent.",
        "TUM geometry/query evidence is explicitly separated from navigation-protocol evidence.",
        "No learned N3 map exists.",
        "No learned N2 map exists.",
        "No universal numeric gate is justified by current evidence.",
        f"Execution counts are frozen in run_manifest.json: `{json.dumps(manifest['counts'], sort_keys=True)}`.",
        f"FINAL_STATUS={decision['FINAL_STATUS']}.",
        f"FINAL_DECISION={decision['FINAL_DECISION']}.",
        f"Only next task={decision['Only_next_task']}; ETH3D training remains unauthorized.",
    ]
    for index, answer in enumerate(answers, 1):
        add(f"{index}. {answer}")
    add("")
    add("## Limitations and decision boundary")
    add("")
    add("This is frozen-map-instance evidence, not algorithm-stability evidence. Five artifacts are unavailable, learned bidirectional multi-tolerance evidence is absent, route/budget/unknown closure is absent for every learned map, and pixels are not treated as independent replicates. These gaps are reported rather than filled by favorable assumptions. Consequently the preregistered tree selects Case C without a universal numeric gate.")
    add("")
    add("## Traced outputs")
    add("")
    add("Machine-readable results are in `run_manifest.json`, `validation_result.json`, the per-map evidence cards, classification matrix, and `eth3d_entry_handoff.json`. Twenty static figures distinguish measured, derived, empirical, unresolved, and not-evaluable evidence.")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("REPORT_COMPLETE", REPORT)


if __name__ == "__main__":
    main()
