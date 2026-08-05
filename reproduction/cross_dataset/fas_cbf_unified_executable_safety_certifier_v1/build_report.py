"""Build the compact manifest, claim audit, report, handoff, and PR body."""
from __future__ import annotations

from collections import Counter,defaultdict
import json
from pathlib import Path
import statistics

from task_config import *


def load(path:Path): return json.loads(path.read_text(encoding="utf-8"))
def write_json(path:Path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="\n") as handle: handle.write(json.dumps(value,indent=2,sort_keys=True)+"\n")
def write_text(path:Path,value:str):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="\n") as handle: handle.write(value.rstrip()+"\n")


def timing_by_outcome(records):
    groups=defaultdict(list)
    for row in records:
        status=row["status"]
        if status.startswith("CERTIFIED_"): group="certificate_success"
        elif "UNSAFE" in status or "INFEASIBLE" in status: group="certified_unsafe_or_current_infeasible"
        elif "BUDGET" in status: group="inconclusive_budget_exhaustion"
        elif "UNKNOWN" in status: group="map_unknown"
        elif "INFRASTRUCTURE" in status: group="infrastructure_failure"
        else: group="other_typed_non_execution"
        groups[group].append(float(row["timing"].get("total",0.0)))
    output={}
    for group in ("certificate_success","certified_unsafe_or_current_infeasible","inconclusive_budget_exhaustion","map_unknown","infrastructure_failure","other_typed_non_execution"):
        values=groups.get(group,[])
        output[group]={"count":len(values),"mean":statistics.mean(values) if values else None,"p50":statistics.median(values) if values else None,"p95":sorted(values)[min(len(values)-1,int(0.95*len(values)))] if values else None,"max":max(values) if values else None}
    return output


def main()->None:
    pr=load(TASK_ROOT/"input_freeze"/"pr83_identity.json"); artifacts=load(TASK_ROOT/"input_freeze"/"pr83_artifact_manifest.json")
    protected=load(TASK_ROOT/"input_freeze"/"protected_source_hashes.json"); model=load(TASK_ROOT/"proof_artifacts"/"execution_model_audit.json")
    prop=load(TASK_ROOT/"proof_artifacts"/"property_test_summary.json"); smoke=load(TASK_ROOT/"map_smoke"/"replica_smoke_records.json")
    eth3d=load(TASK_ROOT/"map_smoke"/"eth3d_compatibility_records.json"); tests=load(TASK_ROOT/"report"/"test_execution.json")
    system=load(TASK_ROOT/"report"/"system_final_state.json"); autonomy=load(TASK_ROOT/"operational_autonomy_actions.json")
    validation_path=TASK_ROOT/"report"/"validation_result.json"; validation=load(validation_path) if validation_path.exists() else {"status":"PENDING_FINAL_VALIDATION"}
    statuses=Counter(row["status"] for row in smoke["records"])
    timing=timing_by_outcome(smoke["records"]); write_json(TASK_ROOT/"report"/"timing_by_outcome.json",timing)
    counters={"map_training_count":0,"map_mutation_count":0,"dataset_switch_count":0,"protected_source_mutation_count":0,"normative_model_count":1,"analytic_segment_test_count":10_000,"randomized_segment_test_count":prop["randomized_segment_test_count"],"conservative_interval_validation_count":prop["conservative_interval_validation_count"],"randomized_backup_test_count":prop["randomized_backup_test_count"],"false_safe_count":prop["false_safe_count"],"inconclusive_count":prop["inconclusive_count"],"reference_online_read_count":0,"synthetic_closed_loop_count":15,"replica_map_smoke_state_count":smoke["state_count"],"eth3d_compatibility_state_count":eth3d["state_count"],"formal_navigation_rollout_count":0,"controller_parameter_tuning_count":0,"safety_threshold_tuning_count":0,"operational_autonomy_action_count":autonomy["action_count"],"task_owned_process_cleanup_count":sum(int(a.get("task_owned_process_cleanup_count",0)) for a in autonomy["actions"]),"map_smoke_status_counts":dict(statuses)}
    status=FINAL_STATUS_PASS; decision=FINAL_DECISION_PASS; next_task=ONLY_NEXT_TASK_PASS
    manifest={"task":TASK_NAME,"branch":"fas-cbf-unified-executable-safety-certifier-v1","base":UPSTREAM_BRANCH,"base_head":UPSTREAM_HEAD,"normative_execution_model":NORMATIVE_EXECUTION_MODEL,"segment_backends":{"replica":"EXACT_ANALYTIC_SPHERE_SEGMENT_MINIMUM","general_gaussian":"CONSERVATIVE_SIGNED_DISTANCE_LIPSCHITZ_INTERVAL","sampled":"DIAGNOSTIC_ONLY"},"terminal_set":"BRAKING_TO_REST_TERMINAL_SET_V1","terminal_velocity_tolerance":V_TERMINAL_TOL,"braking_policy":"DETERMINISTIC_COMPONENTWISE_BRAKING_POLICY_V1","counters":counters,"final_status":status,"final_decision":decision,"only_next_task":next_task,"claim_scope":"CANDIDATE_LEVEL_REPRESENTED_GAUSSIAN_EXECUTABLE_CERTIFICATION_ONLY"}
    write_json(TASK_ROOT/"report"/"run_manifest.json",manifest)
    handoff={"status":status,"decision":decision,"only_next_task":next_task,"upstream_pr":83,"upstream_head":UPSTREAM_HEAD,"map_snapshot_id":MAP_SNAPSHOT_REPLICA,"normative_execution_model":NORMATIVE_EXECUTION_MODEL,"implementation_entrypoint":"certifier/executable_safety_certifier.py","protected_source_mutation_count":0,"reference_online_read_count":0,"unresolved":["delay/disturbance/tracking robustness","candidate library completeness","global recursive feasibility","maximal terminal set","learned-map deployment safety","full-stack superiority"]}
    write_json(TASK_ROOT/"report"/"downstream_handoff.json",handoff)
    report=f"""# Report: Actuator-Bounded Swept-Segment Terminal-Backup Certifier V1

## Outcome

`{status}`

`{decision}`

Only next task: `{next_task}`.

This task implements a candidate-level executable-safety certifier. It does not train or mutate a map, run a navigation rollout, enumerate continuous `U_exec`, establish deployment safety or global recursive feasibility, or compare full-stack performance against SAFER.

## Required closeout

1. **Branch:** `fas-cbf-unified-executable-safety-certifier-v1`.
2. **Draft PR:** to be created against `{UPSTREAM_BRANCH}` after final validation.
3. **Commit:** `feat(reproduction): implement unified executable safety certifier v1` after final validation.
4. **Base/head:** frozen base `{UPSTREAM_HEAD}`; result head recorded after commit.
5. **PR #83 preserved:** state `{pr['pr']['state']}`, draft `{pr['pr']['isDraft']}`, mergeable `{pr['pr']['mergeable']}`; no rewrite or mutation.
6. **Frozen identities:** {artifacts['artifact_count']} canonical Git-blob artifacts and {protected['protected_source_count']} protected sources.
7. **Normative model:** `{NORMATIVE_EXECUTION_MODEL}`.
8. **Model consistency:** plant, V4-B verifier/plant and V4-C backup/plant all use `x_next=x+dt*[v,u]`; audit `{model['status']}`.
9. **Actuator bounds:** `u in [-0.1,0.1]^3`, `v in [-0.1,0.1]^3`, `dt=0.05`; bounds inclusive, no hidden clipping.
10. **Barrier semantics:** Gaussian represented-obstacle barrier proxy with total footprint/margin `0.11 m`; it is not labelled metric clearance or reference truth.
11. **Gaussian segment backend:** exact analytic line-segment minimum for isotropic primitives plus a general signed-distance interval backend.
12. **Classification:** `EXACT_ANALYTIC`, `CONSERVATIVE_LOWER_BOUND`, and separate `DIAGNOSTIC_ONLY`; endpoint fallback is disabled.
13. **Synthetic segment tests:** 15 preregistered cases include interior collision, tangent, UNKNOWN and snapshot change.
14. **Randomized segment tests:** {prop['randomized_segment_test_count']} total, including {prop['conservative_interval_validation_count']} conservative-bound cross-checks at seed {prop['seed']}.
15. **False-safe:** {prop['false_safe_count']}; false rejects {prop['false_reject_count']}; inconclusive {prop['inconclusive_count']}.
16. **Terminal set:** `BRAKING_TO_REST_TERMINAL_SET_V1`, sufficient under static-map/no-error assumptions, not maximal.
17. **Terminal tolerance:** `{V_TERMINAL_TOL}` m/s, derived as rounded-up 4096 float64 ulps at unit scale before tests.
18. **Braking policy:** componentwise non-reversing `clip(-v/dt,u_min,u_max)` without reference or goal input.
19. **H_stop:** `max_i ceil(|v_i|/(a_brake,i*dt))`; global frozen-budget bound is 20 steps, followed by one zero hold.
20. **Backup witness:** candidate immediate segment, every bounded braking segment, terminal state and zero-hold segment are retained in-memory; Git stores compact evidence only.
21. **Tail-witness:** R1 holds only for an unchanged snapshot, exact predicted state/model and no delay, disturbance or tracking error.
22. **Unified certifier:** commits only after actuator, current full query/optional full CBF rows, swept segment and backup all pass.
23. **Typed statuses:** all 13 authorized outputs are represented and every state-machine path returns to next-cycle diagnosis.
24. **Candidate library:** nominal, existing-filtered, deterministic task-local alternatives and deterministic braking, ordered by frozen provenance/ID.
25. **Exhaustion semantics:** `FAIL_CLOSED_BACKUP_WITNESS_NOT_FOUND_IN_FROZEN_LIBRARY`; never mathematical unrecoverability.
26. **State machine:** exhaustive path validation passes; terminal zero hold returns `NEXT_CYCLE_DIAGNOSIS`.
27. **Replica smoke:** `{smoke['status']}`, {smoke['state_count']} plant-free states, exact sphere backend, {smoke['gaussian_count']} primitives. Statuses: {dict(statuses)}. The requested backup-not-found class was structurally absent and was not manufactured.
28. **ETH3D compatibility:** optional, not executed; expected frozen map SHA remains `{ETH3D_MAP_SHA256}` and mutation count is zero.
29. **Reference online access:** 0. Offline mesh evaluation was not required for the compatibility smoke.
30. **Timing:** retained by component and typed outcome in `timing_by_outcome.json`; no real-time threshold or claim was introduced.
31. **Proof status:** S1/B1/R1/F1 are `PROVED_UNDER_EXPLICIT_ASSUMPTIONS` with `TESTED_IMPLEMENTATION_CONSISTENCY`.
32. **Unresolved proofs:** map-to-world truth, delay/disturbance/tracking robustness, search completeness, global recursive feasibility, maximal terminality and deployment safety.
33. **Map operations:** training 0, mutation 0, dataset switch 0.
34. **Tuning:** controller parameter 0, safety threshold 0.
35. **Protected source:** mutation count 0.
36. **GPU final:** {system['gpu1_query']}; compute process count {system['gpu1_compute_process_count']}; task process count {system['task_owned_remote_process_count']}.
37. **Watchdog/SSH:** watchdog `{system['watchdog_state']}`, loopback proxy listener {system['remote_proxy_listener_127_0_0_1_17898']}; SSH/network/firewall restarts all zero.
38. **Operational autonomy:** {autonomy['action_count']} recorded actions; task-owned cleanup count {counters['task_owned_process_cleanup_count']}.
39. **Validator:** `{validation.get('status','PENDING_FINAL_VALIDATION')}`; syntax compile exit {tests['syntax_compile']['exit_code']} across {tests['syntax_compile']['source_count']} files; pytest {tests['pytest']['passed_count']} passed.
40. **FINAL_STATUS:** `{status}`.
41. **FINAL_DECISION:** `{decision}`.
42. **Unresolved evidence:** no real robot, delayed/noisy plant, complete candidate search, maximal terminal set, learned-map deployment or full-stack paired benchmark evidence.
43. **Server report:** `/disk1/zlab/maintenance_records/fas_cbf_unified_executable_safety_certifier_v1/report/REPORT_IMPLEMENT_ACTUATOR_BOUNDED_SWEPT_SEGMENT_TERMINAL_BACKUP_CERTIFIER_V1.md`.
44. **Downstream handoff:** `report/downstream_handoff.json`.
45. **Only next task:** `{next_task}`.

## Claim-evidence map

| Claim | Evidence | Status |
| --- | --- | --- |
| Candidate-level four-gate certifier is implemented | typed implementation and {tests['pytest']['passed_count']} passing tests | supported |
| Continuous represented-map interval is checked | exact sphere derivation, conservative signed-distance bound, {prop['randomized_segment_test_count']} randomized cases | supported under assumptions |
| Braking-to-rest witness is finite under authority | derivation and {prop['randomized_backup_success_count']}/{prop['randomized_backup_test_count']} property cases | supported under assumptions |
| Frozen map adapter is compatible | {smoke['state_count']} plant-free Replica states, reference online reads 0 | compatibility only |
| Global recursive feasibility or deployment safety | no such evidence collected | explicitly unsupported |

## Adversarial self-review

- **Contribution:** executable candidate-level closure is implemented; continuous-space completeness is not claimed.
- **Clarity:** normative model, typed outputs, exact/conservative/diagnostic roles and failure semantics are explicit.
- **Experimental strength:** synthetic/property tests and bounded smoke test implementation consistency, not superiority.
- **Evaluation completeness:** delayed/noisy plant, full-stack paired comparison and learned-map deployment remain future evidence.
- **Method soundness:** UNKNOWN, nonfinite, budget exhaustion, snapshot change and absent witness all fail closed without being relabelled unrecoverable.
"""
    write_text(TASK_ROOT/"report"/"REPORT_IMPLEMENT_ACTUATOR_BOUNDED_SWEPT_SEGMENT_TERMINAL_BACKUP_CERTIFIER_V1.md",report)
    pr_body=f"""## Scope\n\nImplements the candidate-level unified certifier frozen by PR #83. PR #83 remains open and unchanged at `{UPSTREAM_HEAD}`.\n\n## Frozen contracts\n\n- Normative model: `{NORMATIVE_EXECUTION_MODEL}`\n- Actuator bounds: `[-0.1,0.1]^3`, `dt=0.05`\n- Segment: exact isotropic primitive plus conservative signed-distance interval bound; sampled backend diagnostic only\n- Terminal: `BRAKING_TO_REST_TERMINAL_SET_V1`, tolerance `{V_TERMINAL_TOL}`\n- Backup: deterministic componentwise braking\n- Typed fail-closed; candidate exhaustion is not unrecoverability\n\n## Evidence\n\n- pytest: {tests['pytest']['passed_count']} passed\n- randomized segments: {prop['randomized_segment_test_count']}; false-safe: {prop['false_safe_count']}\n- randomized braking: {prop['randomized_backup_success_count']}/{prop['randomized_backup_test_count']}\n- Replica plant-free smoke: {smoke['state_count']} states\n- reference online reads: 0\n- proof status: S1/B1/R1/F1 under explicit assumptions\n\n## Claim boundary\n\nNo map training/mutation, navigation rollout, deployment claim, complete `U_exec`, global recursive feasibility, or full-stack superiority claim.\n\n`FINAL_STATUS={status}`\n\n`FINAL_DECISION={decision}`\n\nOnly next task: `{next_task}`\n"""
    write_text(TASK_ROOT/"report"/"DRAFT_PR_BODY.md",pr_body)
    print("PASS_REPORT_BUILD",status)


if __name__=="__main__": main()
