# REPORT — Design Active Runtime Assurance Implementation V2

## Decision first

`PASS_ACTIVE_RUNTIME_ASSURANCE_IMPLEMENTATION_V2_DESIGN`. The frozen PR #107–#114 contracts admit an additive implementation with no production edit. The blueprint has one selection owner (`Supervisor.arbitrate`), one plant owner (`PlantCommitAdapter.commit`), total 43-rule state-machine mapping, V2-only geometry/actuator injection, explicit first-cycle and token handoff behavior, typed failure routes, a numeric deadline startup gate, and a one-way immutable trace-to-oracle boundary.

`FINAL_DECISION=FREEZE_ACTIVE_RUNTIME_IMPLEMENTATION_DESIGN_AND_ADVANCE_IMPLEMENTATION_DAG`.

## Integration result

The current runner exposes x_k, goal, PD `u_des`, successful Clarabel QP result, map object/query, trial construction, dt/dynamics, and the exact plant entry. An independent package under `reproduction/runtime/active_runtime_assurance_v2/` can therefore compose the V2 runtime without modifying `run.py`, `cbf/`, `dynamics/`, or `splat/`. `run.py` remains `REFERENCE_BASELINE`.

The primary proposal is the successful finite Clarabel CBF-QP result. The QP has no actuator box constraints, so C0 must apply the PR #109 inclusive bounds to the unchanged proposal. Violation rejects; clipping is prohibited. Solver failure cannot inherit the legacy `u_des` return path.

## Cycle architecture

Startup first verifies map, geometry, actuator, dynamics/timebase, deadline-profile presence, terminal contract, backup-token schema, transition hash, trace schema, and oracle boundary. I0a then performs the full-query start admission. No I0b repair primitive is authorized by this design; an inadmissible start reaches the no-action boundary.

Per cycle, L1 certifies the candidate-independent immediate segment once. Each primary or lawful alternative obtains a fresh binding to that immutable cycle result and then enters C0 → L2 → L3. L2 uses the PR #108 G3 represented-map authority, 0.025 m effective certification radius, and rho_seg=0. Historical V1 0.11 m loaders are forbidden. L3 PASS prepares, but does not activate, an immutable witness bundle.

The Supervisor arbitrates certified navigation with prepared token, retained valid backup, eligible current certified terminal, then assurance boundary. Successful navigation commit activates its exact bundle for k+1 atomically; successful backup commit advances the old cursor once. Failed commits do not mutate either. Assurance boundary performs no plant call.

## Alternatives, terminal, deadline

Static inventory found no native sibling candidates. `u_des` is not an alternative. L4 therefore returns `NO_ALTERNATIVE_AVAILABLE`; it cannot synthesize, perturb, interpolate, or sample controls. Terminal membership, certificate, eligibility, selection, and commit remain separate. Exact zero is terminal only by Supervisor-assigned role/identity. Goal-hold stays disabled because runtime authority is unresolved.

The Supervisor owns deadline policy. ACTIVE startup rejects a missing `RuntimeDeadlineProfile` with `DEADLINE_PROFILE_REQUIRED`; this design does not invent numbers. After expiry, no new search begins. Fake clocks are restricted to unit/BYPASS QA and establish no timing performance.

## Trace and evaluation isolation

The runtime emits exact typed facts and explicit action roles, then finalizes a canonical immutable trace lock. Only after that lock may the independent PR #114 post-hoc oracle run. There is no oracle-to-runtime edge, and runtime code may not import oracle decision logic. This keeps certification evidence distinct from final outcome labels.

## Validation and scope

All 43 frozen transition rows map exactly once. ARI-01–ARI-30 and 28 design scenarios are complete. The abstract model checker has zero counterexamples; the stdlib validator passes all design gates. The reviewer verdict is `PASS_ACTIVE_RUNTIME_ASSURANCE_IMPLEMENTATION_DESIGN_FROZEN`.

Remaining gates are operational rather than hidden contract edits: implement code and unit/static tests; pass OFF/BYPASS trace equivalence; pass contract conformance; obtain separate authorization for a tiny engineering smoke; freeze numeric deadline/statistics/protocol; then authorize one final100. No active runtime, GPU, rollout, smoke, pilot, benchmark, formal collection, or tuning occurred here. No efficacy, collision-reduction, real-time, physical-safe-stop, or deployment claim is supported.

Only next task: `IMPLEMENT_ACTIVE_RUNTIME_ASSURANCE_V2`.
