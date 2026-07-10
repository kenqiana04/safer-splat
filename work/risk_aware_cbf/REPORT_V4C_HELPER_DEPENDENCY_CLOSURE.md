# REPORT: V4-C Helper Dependency Closure Restoration

## 1. Purpose

This task restores the original V4-C runner's two direct helper dependencies,
audits their minimal dependency closure, validates a non-executing shadow
interface, and repeats R1 Stage 0. It does not run a new scientific experiment.

## 2. Direct Helper Dependencies

The V4-C runner directly imports
`run_risk_aware_v1_pre_cbf_comparison.py` and
`run_v4b_corrective_dt_filter.py`. Both exact files were restored. AST analysis
found 25 referenced helper symbols, all present after restoration.

## 3. Provenance

The Priority-1 source was `/disk1/zlab/projects/safer-splat` at
`master@57c55485e357343c3d166a9123ab9a9275c12067`.

| Helper | SHA256 | Source status | Evidence |
| --- | --- | --- | --- |
| V1 pre-CBF | `e846ff625ed52d197844bdb2f56df72ab8e09cb3d94f0b42724520112268176e` | untracked | Priority-1 source plus six byte-identical local copies |
| V4-B corrective filter | `573c0587e238eb160928a8b5349239fc852af91791877d87f6abe55e0062f862` | untracked | Priority-1 source plus two byte-identical local copies |

Source and target hashes match. Because the source files were untracked, this
report does not claim that Git commit `57c5548` tracks their contents.

## 4. Static Dependency Graph

The AST-only audit found 59 direct import edges. The closure contains 12
standard-library modules, six third-party environment dependencies, and three
local modules already present in the branch: `cbf.cbf_utils`,
`dynamics.systems`, and `splat.gsplat_utils`.

## 5. Minimal Restored Closure

Two direct helpers were restored byte-for-byte. Zero additional transitive
local Python files were required. The closure stayed below the eight-file cap
and did not restore an unrelated directory, result, trace, image, or binary.

## 6. Importability and Side Effects

The helpers, V4-C runner, and official smoke wrapper pass `py_compile` in the
4090 `safer_splat_official` environment. Helper and runner imports pass, and
all four `--help` commands return successfully without a formal trial.

Raw helper loading initializes CUDA and changes Python RNG state through
dependency initialization. It does not start an experiment or write repository
files. The shadow adapter restores Python, NumPy, Torch, and already-initialized
CUDA RNG states around lazy loading and evaluation. This bounded initialization
is recorded, not hidden.

## 7. Required Symbol Validation

Runtime reflection checked all 25 AST-discovered references, including
`RiskScoreTable`, `make_start_goal_configs`, `nominal_control`, `cuda_sync`,
`query_h`, `query_h_and_critical`, `clamp_control`, `unit_or_zero`,
`parse_csv_floats`, `bool_csv`, `CsvAppender`, `start_for_trial`, and
`make_cbf`. All symbols exist with inspectable source metadata; failures: 0.

## 8. Shadow Adapter

`v4c_recovery_shadow_interface.py` is a thin, nonfunctional adapter. It creates
the named H3_N128 namespace, clones context tensors, invokes the original
`generate_sequences`, `evaluate_sequences`, and `rollout_sequence` functions,
and packages compact results. It does not reimplement generation, cost,
ranking, rollout, or recovery selection and never applies the selected control
to formal execution.

## 9. Equivalence Check

A deterministic interface check used the actual flight GSplat checkpoint and
official trial 14 initial state. Direct original-function evaluation and the
adapter matched on 22 checks, including configuration, inputs, RNG policy,
candidate count and digests, selection, H sequence, minimum H, cost, progress,
state immutability, formal-control non-modification, and RNG restoration.
Critical mismatches: 0. This is interface equivalence, not recovery-performance
validation; `h` is not meter clearance.

## 10. R1 Stage-0 Reassessment

M0, M1, and M2 are `shadow_evaluable`. M2 now has callable original candidate
generation and evaluation, cloned recovery state, fixed H3_N128 configuration,
common H-step comparison, and a comparable diagnostic progress proxy. M3
remains `interface_only` and excluded because no provenance-confirmed stop
contract was found. No five-context R1 shadow audit was run.

## 11. Decision

`closure_decision = dependency_closure_restored_r1_stage0_ready`

The preregistered R1 shadow audit is executable in a separate task. This
decision establishes interface readiness only.

## 12. Claim Boundaries

- No new scientific experiment or formal trajectory was run.
- No active R1 or active V4-C command was executed.
- No recovery performance, warning reduction, completion improvement, benchmark,
  real-robot, global safety, or theorem claim is made.
- No core algorithm source was modified.

The current task restores the original V4-C dependency closure and reassesses interface readiness; it does not revalidate recovery performance or R1 effectiveness.

The restored dependency closure makes the preregistered R1 shadow audit executable in a separate task; no shadow or active effectiveness has yet been established.
