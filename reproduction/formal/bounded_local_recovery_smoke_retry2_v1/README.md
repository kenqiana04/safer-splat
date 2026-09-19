# Bounded Local Recovery Smoke Retry2 V1

This directory freezes an engineering-only Retry2 Smoke protocol. It does not execute a trial during the freeze task and does not establish efficacy, noninferiority, physical safety, deployment readiness, or a real-time guarantee.

## Why these trials

The fixed cohort is `[15, 45, 75]` in that order. Retry1 naturally reached bounded-recovery eligibility at trial/cycle `15/202`, `45/168`, and `75/281`; each witness reached Recovery rank-0 C0 PASS and then failed in Recovery L2 because flat canonical L2 evidence collided. Reusing the same cohort is the direct before/after engineering comparison and is not post-hoc parameter selection.

Retry1 remains `INCONCLUSIVE_RECOVERY_SEARCH_EXERCISED_BUT_NO_RECOVERY_COMMIT`. The scientific verdict remains `FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE`.

## Repair authority and scope

Runtime authority is repair HEAD `2102c8401b61ca8fe74123ab51e8fc9c27ed0895`. The repair preserves legacy Primary flat `canonical_l2_*` facts, adds deterministic candidate-scoped `canonical_l2_candidate_evidence`, and preserves conflicting same-scope rewrite rejection. Retry2 checks that the old collision does not recur, that Recovery L2 produces typed results, and that any selected Recovery candidate is fully certified before PlantCommit.

The recovery contract remains six F32 axis extrema, order `+x,-x,+y,-y,+z,-z`, magnitude `0.1`, with 0.015 q hard radius, zero runtime margin/rho, and epsilon null. The protocol has no Reference arm, NI analysis, formal85 execution, scientific oracle, or parameter tuning.

## Frozen future execution

Future result root:

`/disk1/zlab/v3_repair_records/bounded_local_recovery_smoke_retry2_v1_20260919`

Future tmux session:

`bounded_local_recovery_smoke_retry2_v1`

Exact authorization token:

`EXECUTE_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_V1`

The future execution task must run from the worktree root:

```bash
cd /disk1/zlab/v3_repair_worktrees/safer-splat-freeze-bounded-local-recovery-smoke-retry2-protocol-v1
/disk1/zlab/conda_envs/safer_splat_official/bin/python \
  reproduction/formal/bounded_local_recovery_smoke_retry2_v1/validate_bounded_local_recovery_smoke_retry2_v1.py \
  --mode prelaunch
/disk1/zlab/conda_envs/safer_splat_official/bin/python \
  reproduction/formal/bounded_local_recovery_smoke_retry2_v1/launch_bounded_local_recovery_smoke_retry2_v1.py \
  --launch --authorize-execution EXECUTE_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_V1
```

If the result root already exists, do not relaunch. Trials are serial, use separate child processes, and have no automatic retry. Any child failure or missing runtime trace lock stops the batch.

## Read-only monitoring

```bash
/disk1/zlab/conda_envs/safer_splat_official/bin/python \
  reproduction/formal/bounded_local_recovery_smoke_retry2_v1/monitor_bounded_local_recovery_smoke_retry2_v1.py
```

## Future post-run analysis

The analyzer must also be invoked from this worktree root; it additionally sets all repository paths internally and never executes Nerfstudio from the task directory:

```bash
cd /disk1/zlab/v3_repair_worktrees/safer-splat-freeze-bounded-local-recovery-smoke-retry2-protocol-v1
/disk1/zlab/conda_envs/safer_splat_official/bin/python \
  reproduction/formal/bounded_local_recovery_smoke_retry2_v1/analyze_bounded_local_recovery_smoke_retry2_v1.py \
  --postrun-authorized
```

Only the later `EXECUTE_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_V1` task may use the launch command.
