# Implementation Plan: Frozen-Map FAS-CBF Stress Activation V2

## Scope and invariants

- Base exactly on PR #80 head `a05f8e1eca4c400a86583eb97fcce5be32062a0d` in the isolated branch `eth3d-fas-cbf-stress-scenario-activation-v1`.
- Preserve the PR #80 result tree and report byte-for-byte; use one frozen ETH3D map, one dataset, one scene, and the existing M0-M4 implementations and scientific constants.
- Never use formal rollout outcomes to select, remove, relabel, or rank V2 scenarios. Reference geometry is restricted to offline validity/evaluation labels and never enters a controller decision.
- Fail closed before formal execution if lineage, identities, V1 semantic recovery, stage quotas, three-process registry determinism, method identity, no-reference-leakage, or smoke consistency fails.

## Execution sequence

1. Freeze PR #80, map, reference, protocol, code, data, environment, GPU, and proxy/watchdog identities into task-owned evidence; verify all expected SHA-256 values and record zero map/dataset/method mutation.
2. Reconstruct V1 terminal, completion, progress, activation, stage-entry, and aggregation semantics from all 500 compact/raw terminal records. Emit the required JSON/CSV/Markdown reconciliation artifacts without changing V1.
3. Implement a plant-free shadow pipeline using exact PR #80 Start-Safe, feasibility-aware reduction, QP, sampled-data verifier, and predictive-recovery functions. Prove a fixed non-triggering control probe is numerically identical to PR #80.
4. Deterministically generate candidate states from PR #80 scenarios, PR #79 nodes, reference/critical-Gaussian offsets, barrier bands, map/reference discrepancy states, and high-density states using seed 20260805. Evaluate candidates in stable order and stop as soon as every group has a deterministic surplus, or at the 200000-state engineering ceiling.
5. Select 20 scenarios per G0-G4 strictly from shadow-stage properties and the frozen ranking rules. Validate reference start/goal validity, map-query finiteness, activation quotas, group strata, no formal metric fields, method-independent sharing, and source diversity.
6. Generate the complete registry in three fresh processes; require identical raw SHA-256 bytes. Lock the registry and record its identity before any controller smoke/formal run.
7. Run 50 smoke records (first two scenarios per group by all five methods). Reconcile actual stage logging against the shadow records and prove terminal semantics, identities, no reference leakage, and no mutation. Any logger/shadow-only correction requires rebuilding and relocking the whole registry.
8. Run exactly 500 formal records sequentially (100 shared scenarios by M0-M4), preserving every terminal failure and using the required mutually exclusive terminal enum. Verify 500 terminal records, zero infrastructure failures, and immutable registry/method/map identities.
9. Analyze scenario-grain paired effects, terminal transitions, 10000-resample deterministic bootstrap intervals, activation, reference safety, progress, feasibility, constraint reduction, DT/recovery evidence, runtime, smoothness, map credibility, and failure cases. Apply only the preregistered module/decision rules.
10. Generate 24 required PNG figures, compact evidence artifacts, validation result, technical report, downstream handoff, and execution counters. Validate internal totals, hashes, claim boundaries, no large/raw forbidden artifacts, final GPU cleanliness, and watchdog/SSH health.
11. Copy only the generated Markdown report to `C:/Users/zlab/Desktop/REPORT`, stage only this task directory, commit, push, create the required Open Draft PR against the PR #80 branch, and verify its head/base/state.

## Verification gates

- V1 semantic artifacts account for all 500 records and explicitly distinguish activation, stage entry, terminal state, completion, success, and progress aggregation.
- Registry quotas: G0 H1/H3/H4 <=2; G1 H1 >=16 and projection success >=12; G2 H2 >=16; G3 DT >=16; G4 recovery >=16 and recoverable >=12.
- Registry: 100 unique shared scenarios, 20 per group, three fresh-process byte identities equal, no formal result fields, V1/map identities unchanged.
- Smoke: 50/50 terminal, shadow/actual trigger agreement, identity and leakage checks pass.
- Formal: 500/500 terminal, 100 per method, 100 per group across methods, no scenario deletion/tuning, no infrastructure terminal.
- Report and validator must agree on the exact final status, decision, only-next-task, module categories, collisions, counters, and unresolved evidence.
