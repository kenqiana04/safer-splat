# Paper-Ready Theoretical Contribution Insert

## 1. Introduction Insert

GSplat-based control barrier function filters provide a useful interface
between a scene representation and online action correction. Their standard
per-step formulation, however, addresses only one part of deployment-oriented
navigation safety. Solving an instantaneous CBF-QP does not determine whether
the robot begins from an admissible state, whether the constrained filter
remains feasible under the selected bounds, or whether the filtered action
retains sufficient safety margin after sampled-data execution. These
distinctions are particularly important because solver infeasibility, a
finite-horizon margin warning, and geometric collision are different outcomes
and require different evidence.

We identify four deployment-relevant failure modes: start-state unsafety,
CBF-QP feasibility failure, sampled-data margin risk, and recovery
insufficiency. The first two concern whether normal filtering can begin and
continue from a valid state; the third concerns finite-step behavior that is
not captured by an instantaneous filtering result; and the fourth separates
risk detection from an executable response. This taxonomy provides a common
structure for stating assumptions, observable failure conditions, and claim
boundaries.

Based on this taxonomy, we formulate a planner-agnostic safety assurance layer
for GSplat-based navigation. The layer augments a SAFER-style GSplat CBF
filtering baseline with Certified Feasibility-Aware Start-Safe CBF, H-step
Discrete-Time Verification, and optional triggered V4-C Predictive Recovery.
It consumes a nominal command from an external or baseline controller and does
not introduce a global planner, local planner, localization method, or
four-wheel-specific dynamics model. Its assurances are module-level and
conditional on the repository safety field, selected dynamics, finite horizon,
and tested configuration; they are not presented as a global safety theorem.

## 2. Contribution Insert

1. We identify four deployment-relevant failure modes in GSplat CBF navigation
   safety: start-state unsafety, CBF-QP feasibility failure, sampled-data margin
   risk, and recovery insufficiency.
2. We propose a planner-agnostic safety assurance layer that augments a
   SAFER-style GSplat CBF filter with start-state feasibility certification,
   H-step discrete-time verification, and optional triggered predictive
   recovery.
3. We define module-level assurance contracts that clarify the input, output,
   assumptions, guarantee scope, failure condition, and non-claims of each
   component, thereby preventing claims beyond the tested simulation and
   deployment settings.
4. We organize the available simulation evidence under this framework and
   provide a real-robot interface contract and deployment plan for later
   validation on a mobile robot platform; we do not claim completed real-world
   validation.

## 3. Method Insert

At each control update, an external navigation source or the baseline
goal-directed controller supplies a nominal command \(u_{\mathrm{nom}}\). The
existing CBF-QP consumes the current state and nominal command and returns an
instantaneously filtered command \(u_{\mathrm{safe}}\) together with solver
status. Before normal execution, Start-Safe certification evaluates the
initial state under the repository GSplat ellipsoid safety field; an
inadmissible state is either repaired and revalidated through the configured
full-query procedure or rejected. During execution, H-step Discrete-Time
Verification rolls out \(u_{\mathrm{safe}}\) under the selected sampled-data
dynamics and reports the predicted minimum safety value and a warning when it
falls below the configured margin. If enabled, V4-C Predictive Recovery is
triggered only by the declared warning condition, evaluates candidate actions
or short sequences, and executes the first action of the selected candidate
before the pipeline re-evaluates the next state. A real robot requires a
separate pose, frame-calibration, command-conversion, robot-consistent rollout,
logging, and emergency-stop adapter; the present 3D double-integrator
simulation is not four-wheel dynamics validation.

## 4. Discussion Insert

The framework intentionally does not introduce a new planner because the
deployment gap addressed here lies between nominal command generation and
safe sampled-data execution. Keeping the nominal-command interface external
makes the assurance layer applicable to different navigation stacks without
claiming their planning or localization performance. We also avoid a global
safety claim: Start-Safe is scoped to initial-state validation under the
repository safety field, the CBF-QP result is instantaneous, DT Verification
is finite-horizon and model-dependent, and V4-C is an empirical triggered
response in tested settings. Adaptive V1, FC-Aware V1, and primitive
MPC-style recovery remain diagnostic or ablation branches rather than parts of
the final method. The failure-mode taxonomy strengthens the method by assigning
each retained module a distinct problem, contract, metric set, and
non-claim, replacing an unstructured wrapper narrative with a coherent
assurance architecture.
