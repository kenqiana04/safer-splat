# L2/H1 On-Policy Shadow Observation Design V1

This directory freezes a prospective observation protocol; it contains no on-policy data and no production instrumentation. The design answers the PR #95 evidence gaps with an immutable post-commit payload, a bounded nonblocking queue, and an authority-isolated shadow worker.

**Boundary:** DESIGN ONLY | NO ON-POLICY COLLECTION | NO CONTROLLER AUTHORITY | NO DECISION FEEDBACK | NO PERFORMANCE CLAIM.

The primary cohort is the controller-selected/executed candidate. Native non-executed candidates are secondary and are recorded only if they already exist before observation. Synthetic candidate count is permanently zero. Observer failure reduces observation completeness but never changes the frozen controller path.

The design selects **Option A: post-commit in-process read-only tap with an out-of-process shadow worker**. The tap is a future instrumentation-only hook after the selected action is accepted and before plant propagation. It performs only immutable copying and `enqueue_nowait`; the worker runs the frozen L0/L1/L2 observation stages and writes append-only results. There is no result-return API.

The frozen planning environment is the mature Stonehenge baseline in `run.py`: 100 deterministic indexed trials, `dt=0.05`, 500-step cap, and a static GSplat config reference. A future implementation must freeze the exact trial manifest and map content hashes before equivalence or collection. PR #89's locked E5 one-step registry is audit context, not a substitute for the on-policy rollout manifest.

Run the design-only validator:

```text
python -B reproduction/design/l2_h1_on_policy_shadow_observation_v1/validate_on_policy_shadow_observation_design_v1.py
```

Expected result: `PASS_L2_H1_ON_POLICY_SHADOW_OBSERVATION_DESIGN_VALIDATION`.
