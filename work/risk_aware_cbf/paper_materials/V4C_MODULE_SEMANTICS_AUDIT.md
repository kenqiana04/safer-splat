# V4-C H-Step Predictive Recovery: Module Semantics Audit

## Scope

This audit treats V4-C as an independent recovery module. It neither selects
among R1 modes nor changes CBF-QP, planning, slowdown, or safe-halt semantics.
The source of truth is `run_v4c_hstep_predictive_recovery.py` and the existing
V4-C reports. The recovered V1/V4-B helpers are byte-identical to the
Priority-1 source and let the module import independently: V1 SHA256
`e846ff625ed52d197844bdb2f56df72ab8e09cb3d94f0b42724520112268176e`; V4-B
SHA256 `573c0587e238eb160928a8b5349239fc852af91791877d87f6abe55e0062f862`.

## Input Contract

| Input | Meaning | Source use |
| --- | --- | --- |
| `x` | six-dimensional position/velocity state | cloned for candidate rollouts |
| `goal` | six-dimensional goal, with position used for direction and progress | nominal and goal-directed candidates |
| `u_nom` | nominal acceleration-like control | nominal repeated candidate |
| `u_base` | CBF-QP filtered baseline control | repeated baseline, scaled, mixed, and random candidates |
| `u_prev` | prior executed recovery/baseline control or `None` | smoothness cost and previous-control candidates |
| GSplat loader | ellipsoid safety-field and critical-Gaussian queries | horizon `h` and repulsive direction |
| `scene_cfg` | radius and scene-specific configuration | safety query radius |
| args | horizon, margins, family switches, cost weights, seed inputs | activation, generation, evaluation |

The rollout applies Euler double-integrator dynamics on a cloned state. Each
rollout step queries repository GSplat ellipsoid geometry through `query_h`.
`h` is the repository safety-field value, not meter clearance.

## Output Contract

`generate_sequences` returns deduplicated, clamped `SequenceCandidate` objects
containing a source label and an H-by-3 control tensor. `evaluate_sequences`
returns the selected sequence, its first control, all horizon `h` values,
horizon minimum `h`, `recovery_success`, `recovery_failed`, candidate rows, and
selected index. The closed-loop wrapper executes only that first selected
control, then replans at the next step.

## Trigger Contract

V4-C first rolls out repeated `u_base` over H steps. Let `h_base_min` be its
horizon minimum. Activation is:

| Mode | Condition |
| --- | --- |
| `always` | true at every feasible CBF step |
| `on_warning` | `h_base_min < warning_margin` |
| `on_margin_violation` | `h_base_min < dt_margin` |

The established dense-flight settings are H3_N128 and tuned R4_H2_N64, both
using `on_margin_violation` with `dt_margin=0.0005`. This does not establish
that the trigger is optimal or calibrated for other scenes.

## Candidate Families

The generator clamps all controls to `[-0.1, 0.1]` and deduplicates controls by
rounded sequence key.

| Family | Original instances |
| --- | --- |
| repeated baseline | `base_repeated`, `nominal_repeated`, scaled baseline |
| braking | braking and brake-then-base, gains 0.25/0.5/1.0/1.5 |
| repulsive | critical-Gaussian repulsion, base-plus-repulsion, repulse-then-base |
| goal-directed | goal-directed and repulse-then-goal |
| mixed / continuity | previous repeated and smooth previous/base when `u_prev` exists |
| random around base | deterministic local RNG seed from trial and step, then Gaussian perturbations |
| optional CEM | CEM elites and mean when `--use-cem` is enabled |

## Evaluation and Selection

For candidate controls `u_1:H`, V4-C computes

`cost = w_base*base_deviation + w_goal*goal_cost + w_smooth*smooth_cost + w_safety*safety_penalty`.

`base_deviation` is mean squared departure from repeated `u_base`; `goal_cost`
is final position squared distance to goal; `smooth_cost` penalizes consecutive
control changes and first-control departure from `u_prev`; and `safety_penalty`
is the sum of squared positive deficits `max(0, dt_margin-h_t)^2`.

Candidates with `min(h_1:H) >= dt_margin` are feasible. V4-C selects the
minimum-cost feasible candidate. If none is feasible, it selects the candidate
with maximum horizon-minimum `h`, marks `recovery_failed=true`, and still
returns its first control. If the generated set is empty, it falls back to the
repeated baseline and marks failure.

## Computational Contract

Without CEM, evaluation requires one H-step GSplat query sequence per generated
candidate: approximately `N_candidates * H` safety queries, plus the initial
baseline H-step query. CEM adds approximately
`cem_iters * num_sequences * H` safety queries during elite search before its
returned candidates are evaluated. Runtime therefore grows with activation
frequency, candidate count, horizon, and GSplat-query cost.

Existing H3_N128 full100 evidence recorded 236 activations, zero executed
H-step margin violations, zero recovery failures, runtime mean 0.170388 s, and
runtime p95 0.702523 s. Activated steps dominated cost. Existing tuned
R4_H2_N64 full100 evidence recorded 193 activations, zero executed H-step
margin violations, zero recovery failures, runtime mean 0.095952 s, and p95
0.309428 s. These are prior configuration-specific observations, not a proof
that H2/N64 or any candidate family is generally optimal.

## Boundary

V4-C is an optional, triggered sampling-based recovery wrapper. It is not a
planner, a CBF-QP modification, a global safety proof, a meter-clearance
estimator, or an R1 coordinator.
