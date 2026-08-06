"""Build the truthful method-fairness blocker report and Draft PR body."""
from __future__ import annotations

import json

from common import sha256_bytes, write_json, write_text
from task_config import BLOCK_DECISION, BLOCK_NEXT, BLOCK_STATUS, PR84_HEAD, SERVER_TASK_ROOT, TASK_ROOT


def load(relative):
    return json.loads((TASK_ROOT / relative).read_text(encoding="utf-8"))


def main() -> None:
    freeze, map_id, ref_id = load("input_freeze/pr84_identity.json"), load("input_freeze/replica_map_identity.json"), load("input_freeze/reference_mesh_identity.json")
    fairness, methods = load("methods/fairness_audit.json"), load("methods/method_registry.json")
    counts, system = load("audits/execution_count_audit.json")["counters"], load("report/system_final_state.json")
    tests = load("report/test_execution.json")
    validation_path = TASK_ROOT / "report/validation_result.json"
    validation = json.loads(validation_path.read_text(encoding="utf-8")) if validation_path.exists() else {"status": "PENDING_FINAL_VALIDATION"}
    downstream = {
        "status": BLOCK_STATUS, "decision": BLOCK_DECISION, "only_next_task": BLOCK_NEXT,
        "upstream_pr": 84, "upstream_head": PR84_HEAD,
        "missing_frozen_inputs": methods["missing_contract"],
        "required_resolution": "Freeze the concrete alternative-control values, IDs, provenance, size, ordering, and canonical identity before any candidate search.",
        "resume_point": "PHASE_0_METHOD_FAIRNESS_GATE_BEFORE_CANDIDATE_GENERATION",
        "candidate_generation_count": 0, "formal_attempt_count": 0,
    }
    write_json(TASK_ROOT / "report/downstream_handoff.json", downstream)
    report = f"""# Report: Replica GT Executable-Safety Activated Benchmark V1

## Outcome

`{BLOCK_STATUS}`

`{BLOCK_DECISION}`

Only next task: `{BLOCK_NEXT}`.

The benchmark stopped at the preregistered Phase-0 method-fairness gate. PR #84 freezes a deterministic ordering function over caller-supplied `alternative_controls`, but it does not freeze the concrete alternative accelerations, candidate IDs, library size, or canonical library identity. Creating those inputs here would alter B3 after outcomes could be observed and violate the explicit no-library-change boundary. No candidate tuple, stage predicate, registry state, reference outcome, one-step method run, or logical-time episode was executed.

## Required closeout

1. **Branch:** `replica-gt-executable-safety-activated-benchmark-v1`.
2. **Draft PR:** created after final validation against `fas-cbf-unified-executable-safety-certifier-v1`.
3. **Commit:** `test(reproduction): benchmark activated executable-safety gates on Replica GT` after final validation.
4. **Base/head:** PR #84 head `{PR84_HEAD}`; result head recorded in Git/PR metadata after commit.
5. **PR #84 preserved:** `{freeze['pr84']['state']}`, draft `{freeze['pr84']['isDraft']}`, mergeable `{freeze['pr84']['mergeable']}`, unmerged.
6. **Frozen certifier identity:** {freeze['artifact_count']} canonical Git-blob artifacts; manifest `{freeze['artifact_manifest_sha256']}`.
7. **Map identity:** `{map_id['map_snapshot_id']}`, all array/registry checks pass.
8. **Reference identity:** official mesh `{ref_id['assets']['reference_mesh']['sha256']}`; validated oracle assets frozen read-only.
9. **Method matrix:** B0/B1/B2 are definable; B3 is not executable from frozen inputs.
10. **Fairness audit:** `{fairness['status']}`.
11. **Normative model:** `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1` unchanged.
12. **Actuator/robot/margin/dt:** `u,v in [-0.1,0.1]^3`, robot `0.1 m`, margin `0.01 m`, `dt=0.05 s`.
13. **Candidate generator:** guarded and not invoked.
14. **Candidate count:** {counts['candidate_generation_count']} of a frozen maximum {counts['candidate_search_limit']}.
15. **Physical-valid count:** {counts['physical_valid_count']}.
16. **Stage funnel:** zero at every stage because the fairness gate precedes search.
17. **G0-G5 counts:** all zero; these are not outcome rates.
18. **Quota case:** not assigned; quota evaluation requires a valid method matrix.
19. **Registry count:** {counts['registry_state_count']}.
20. **Registry SHA:** not created; no invalid registry was locked.
21. **Three-process rebuild:** not run; rebuild count {counts['registry_rebuild_count']}.
22. **Prelock reference reads:** {counts['prelock_future_reference_read_count']}.
23. **Selection leakage:** `PASS_NO_SELECTION_OCCURRED`; no selection or deletion occurred.
24. **One-step run count:** {counts['one_step_method_run_count']}.
25. **Logical episode count:** {counts['logical_episode_count']}.
26. **Logical step count:** {counts['logical_control_step_count']}.
27. **B0 result:** not executed; no scientific outcome.
28. **B1 result:** not executed; no scientific outcome.
29. **B2 result:** not executed; no scientific outcome.
30. **B3 result:** not executable from the frozen PR #84 inputs.
31. **G1 evidence:** unavailable; no segment-gate causal claim.
32. **G2 evidence:** unavailable; no backup-gate causal claim.
33. **G3 evidence:** unavailable; alternative rescue cannot be evaluated fairly.
34. **G0 over-rejection:** unavailable; no denominator exists.
35. **Terminal semantics:** upstream contract preserved; no terminal state evaluated.
36. **Fail-closed semantics:** no scientific fail-closed result; task blocking is not `SAFE_STOP`.
37. **Represented false-safe:** no trial; count {counts['represented_false_safe_count']} is an execution count, not an estimated rate.
38. **Reference collision:** not evaluated; oracle query count zero.
39. **Map-reference disagreement:** not evaluated; count {counts['map_reference_disagreement_count']}.
40. **Progress:** not evaluated.
41. **Runtime:** no method decision timed; upstream PR #84 timing is not reused as benchmark timing.
42. **50 ms deadline:** not estimable; decision count and miss count are zero, with no real-time claim.
43. **Paired statistics:** no state-level pairs; no tests, effects, CIs, or p-values computed.
44. **H1-H5:** preregistered but all `NOT_TESTED_METHOD_FAIRNESS_BLOCK`.
45. **Unresolved evidence:** every causal gate, rescue, reference, progress, and deadline claim remains unresolved.
46. **Map training/mutation:** {counts['map_training_count']}/{counts['map_mutation_count']}; dataset switch {counts['dataset_switch_count']}.
47. **Tuning:** controller {counts['controller_parameter_tuning_count']}; safety threshold {counts['safety_threshold_tuning_count']}.
48. **Protected-source mutation:** {counts['protected_source_mutation_count']}.
49. **GPU final:** `{system['gpu1_query']}`; compute processes {system['gpu1_compute_process_count']}; task processes {system['task_owned_remote_process_count']}.
50. **Watchdog/SSH:** watchdog `{system['watchdog_state']}`, loopback listener `{system['remote_proxy_listener_127_0_0_1_17898']}`; restart counts zero.
51. **Operational autonomy:** {counts['operational_autonomy_action_count']} recorded actions; task-owned cleanup {counts['task_owned_process_cleanup_count']}.
52. **Validator:** `{validation.get('status', 'PENDING_FINAL_VALIDATION')}`; syntax {tests['syntax_compile']['source_count']} sources, pytest {tests['pytest']['passed_count']} passed.
53. **FINAL_STATUS:** `{BLOCK_STATUS}`.
54. **FINAL_DECISION:** `{BLOCK_DECISION}`.
55. **Server report:** `{SERVER_TASK_ROOT}/report/REPORT_BUILD_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md`.
56. **Downstream handoff:** `report/downstream_handoff.json`.
57. **Only next task:** `{BLOCK_NEXT}`.

## Claim-evidence map

| Claim | Evidence | Status |
| --- | --- | --- |
| PR #84 and external assets retain the required identities | canonical Git blobs and read-only server hashes | supported |
| B0-B2 share definable primary inputs | frozen method/API audit | supported |
| B3 can be compared fairly to B2 | no concrete alternative values, IDs, size, or identity in PR #84 | blocked |
| Any gate improves safety, availability, or progress | no candidate or method execution | unsupported |

## Adversarial self-review

- **Contribution:** this result identifies a reproducibility gap in the method matrix; it is not a performance result.
- **Clarity:** the missing B3 inputs and exact resume prerequisite are explicit.
- **Experimental strength:** no experiment was run after the fairness failure, so no empirical effect is claimed.
- **Evaluation completeness:** H1-H5 remain untested and every result file is marked presearch-blocked.
- **Method soundness:** inventing an alternative library here would change the scientific method and invalidate causal attribution.
"""
    report_path = TASK_ROOT / "report/REPORT_BUILD_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md"
    write_text(report_path, report)
    pr_body = f"""## Scope

Preserves PR #84 at `{PR84_HEAD}` and records a preregistered Phase-0 method-fairness blocker. No candidate search, registry, reference outcome, paired decision, rollout, map mutation, or tuning occurred.

## Frozen identities

- PR #84: Open Draft, unmerged, exact head preserved
- certifier artifacts: {freeze['artifact_count']} canonical Git blobs
- Replica map snapshot: `{map_id['map_snapshot_id']}`
- official reference mesh: `{ref_id['assets']['reference_mesh']['sha256']}`

## Method matrix and blocker

B0, B1, and B2 are definable from frozen inputs. B3 is not: PR #84 freezes the ordering of caller-supplied alternatives, but not their acceleration values, candidate IDs, library size, or canonical identity. Adding them in this task would violate the frozen method contract.

- scenario generation: not started
- group counts: all zero, not outcome rates
- registry SHA: not created
- prelock reference reads: 0
- one-step runs / logical episodes: 0 / 0
- represented false-safe: not evaluated
- alternative rescue: not evaluated
- deadline miss: not estimable
- statistical unit: state or episode; H1-H5 not tested
- fail-closed is not a safe stop; candidate exhaustion is not unrecoverability

`FINAL_STATUS={BLOCK_STATUS}`

`FINAL_DECISION={BLOCK_DECISION}`

Only next task: `{BLOCK_NEXT}`
"""
    write_text(TASK_ROOT / "report/DRAFT_PR_BODY.md", pr_body)
    print("PASS_BLOCKER_REPORT_BUILD", sha256_bytes(report_path.read_bytes()))


if __name__ == "__main__":
    main()
