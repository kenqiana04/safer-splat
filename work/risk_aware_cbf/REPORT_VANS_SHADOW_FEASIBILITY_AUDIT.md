# REPORT: Verification-Aware Nominal Action Selection Shadow Feasibility Audit

## 1. Purpose

This report evaluates whether bounded alternative nominal actions could pass
CBF-QP and H-step verification at naturally observed warning states without
altering the executed control. It is a shadow counterfactual audit, not an
active action-selection experiment.

## 2. Difference from Warning-Streak Slowdown

* slowdown scales post-filter executed command;
* VANS selects pre-filter nominal candidates;
* shadow VANS does not execute its selection.

## 3. Action Semantics

`u_nom` and `u_safe` are 3D torch Tensor commands in the existing
double-integrator control path. Directional candidate support is disabled
because no explicit planar heading/action-plane semantics are grounded.
The candidate set is N0 original, N1 scaled 0.75, and N2 scaled 0.50.

## 4. Method

The formal trajectory executes the baseline no-op `u_safe`. At natural warning
states, the audit evaluates the preregistered nominal candidates on cloned
state with fresh CBF evaluators, then performs H-step counterfactual
verification. Shadow selection is lexicographic and never modifies control.

## 5. Results

| Metric | Value |
| --- | ---: |
| Included contexts | C003, C004, C002, C001, C006 |
| Contexts completed | 5 |
| Candidate set size | 3 |
| Total original warning steps | 189 |
| Total verified alternative steps | 1 |
| Total progress-nonworse verified alternative steps | 0 |
| Total shadow-selection-differs steps | 97 |
| Total potential-warning-avoidance steps | 1 |
| C004 verified alternative steps | 0 |
| C006 verified alternative steps | 0 |
| State isolation all passed | true |

Contexts with verified alternatives: C002.

Contexts with progress-nonworse verified alternatives: none.

## 6. Interpretation

Candidate availability and counterfactual feasibility are distinct from
closed-loop effectiveness and planner performance. Shadow opportunities cannot
be used to claim active warning reduction, completion improvement, or planning
accuracy.

## 7. Relationship to Final SAFC Method

VANS remains outside the core SAFC method. Depending on the decision below, it
is either a bounded optional action-selector prototype candidate, a diagnostic
extension, future work, or inconclusive.

## 8. Decision

`vans_decision = retain_as_diagnostic_extension`

Verified alternatives exist only under limited or tradeoff-heavy conditions; VANS remains diagnostic.

The shadow audit identified counterfactual verified nominal-action opportunities; active closed-loop effectiveness remains unvalidated.

## 9. Claim Boundaries

* no active VANS;
* no executed-command change;
* no warning-reduction claim;
* no completion-improvement claim;
* no planner-improvement claim;
* no benchmark;
* no statistical significance;
* no real-robot validation;
* no global safety guarantee;
* no new CBF theorem.

Verification-Aware Nominal Action Selection has not yet been actively
validated.
