# REPORT: V4-C Executable Artifact Restoration and R1 Interface Reopening

## 1. Purpose

This task restores reproducibility artifacts and reassesses R1 Stage 0
interfaces. It is not a new method experiment, recovery redesign, active R1
evaluation, or R1 shadow-context audit.

## 2. Original Expected Artifacts

The expected artifacts were the V4-C recovery runner, V4-C sweep script, V4-C
analysis script, and the official run.py smoke wrapper. The V4-C reports also
referenced compact summaries, but raw trials, traces, images, and binaries were
not restoration targets.

## 3. Search Scope

Read-only searches covered the 4090 `/disk1/zlab` and home trees, local
Documents/Desktop/Downloads roots, old local clones and archives, all current
Git branches/tags/worktrees, named Git objects, and unreachable objects. The
current local Git clone contained no recoverable named history object.

## 4. Source Provenance

The Priority-1 4090 source is `/disk1/zlab/projects/safer-splat` at
`master@57c55485e357343c3d166a9123ab9a9275c12067`. It supplied all four exact
artifact hashes. July 2 HStep and July 3 Flight100 local archives independently
contain byte-identical V4-C scripts. The July 3 archive also contains the
Flight100 command log identifying the original remote recovery runner path.

| Artifact | SHA256 | Provenance | Restored |
| --- | --- | --- | --- |
| recovery runner | `d710f36d73f953e16588286445e30596887b7559faceccdd81c49e0223d930fe` | confirmed | yes |
| sweep script | `20c896558dc7a65db28d1859b7f79cc8b596dc224868aeccbe980555ff8eb728` | confirmed | yes |
| analysis script | `9dd9c8964334dcc174f669eeb83f4b82cf0ff5433a6a1df454f8270e5b1ecdbf` | confirmed | yes |
| official smoke wrapper | `79ec0933cfc106dbb86be74607c18ecbb99185398cb338c3fdb2527f20ed5ecf` | confirmed | yes |

## 5. Configuration Match

The recovered V4-C runner matches the named H3_N128 configuration: dense
flight, `risk_aware_v1_bestD`, horizon 3, 128 sequences,
`on_margin_violation`, `dt_margin=0.0005`, `warning_margin=0.0008`, and
control scales `0,0.25,0.5,0.75,1.0`. It contains braking, repulsive,
goal-directed, mixed, random-around-base, and repeated-baseline families.

The code rolls out the repeated baseline to detect the H-step margin condition,
selects the lowest weighted-cost feasible sequence, falls back to the largest
horizon minimum safety value when no candidate passes, returns only the first
selected control, and records recovery success/failure. It queries the existing
GSplat safety field; `h` is not interpreted as meter clearance.

## 6. Restoration

The three V4-C scripts were restored under `work/risk_aware_cbf/scripts/`, and
the exact wrapper was restored under `reproduction/scripts/`. Source and target
SHA256 hashes match for all four files. No algorithm logic, defaults, candidate
family, cost, random seed, state transition, or core source was changed.

No raw trace, `trials.csv`, debug CSV, JSONL, trajectory sample, image,
checkpoint, model, or binary was restored.

## 7. Importability and Equivalence

Both restored Python files pass local `py_compile` with pycache redirected
outside the repository. The local default Python lacks `torch`, so local CLI
help cannot load dependencies. In the original 4090
`safer_splat_official` environment, both original artifact imports and both
`--help` commands succeed without executing an experiment.

The original V4-C runner exposes `generate_sequences`, `evaluate_sequences`,
`run_trial`, and `build_parser`. Its candidate rollout clones state. However,
the current Git branch does not contain the original
`run_risk_aware_v1_pre_cbf_comparison.py` or
`run_v4b_corrective_dt_filter.py` imports. Restoring them is outside this
task's allowlist. An adapter would not solve missing imports without extending
scope, so no adapter and no equivalence check were created.

## 8. R1 Stage 0 Reopening

M0 normal and M1 slowdown interfaces are now restored and semantically
auditable. M2 has provenance-confirmed source but is not callable in this Git
branch because the original helper dependencies are absent. M3 remains
interface-only because the double-integrator has velocity and zero acceleration
does not ground a stop command.

The common-horizon comparison and full state-isolation check are therefore not
established in the target branch. R1 Stage 0 was not rerun, and no C003, C004,
C002, C001, or C006 context was executed.

## 9. Decision

`restoration_decision = partially_restored_still_blocked`

The next permissible step is a separate provenance review for the two original
V4-C helper modules, followed by a nonfunctional interface/equivalence task.
This restoration task does not authorize such recovery or refactoring.

## 10. Claim Boundaries

- No new scientific experiment was run.
- No active R1 and no R1 shadow-context audit was run.
- No recovery performance or warning-reduction claim is made.
- No recovery algorithm was reconstructed.
- No planner, real-robot validation, global safety guarantee, or new theorem is
  claimed.

The current task restores reproducibility interfaces; it does not redesign or revalidate V4-C recovery.

The R1 direction remains open, but executable evaluation remains blocked by missing provenance-confirmed artifacts.
