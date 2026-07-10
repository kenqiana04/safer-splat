# REPORT: R1 Verification-Aware Supervisory Mode Selection Shadow Audit

## 1. Purpose

This report evaluates whether the current repository can support a fixed
verification-aware supervisor that compares normal CBF-filtered execution,
warning-gated slowdown, existing V4-C recovery, and a grounded fail-safe halt
interface without changing the formal executed command.

The result is an interface stop at Stage 0. No shadow run was performed because
the current worktree cannot construct or isolate the required M2 recovery mode.

## 2. Difference from Earlier Designs

R1 is not scalar slowdown tuning, magnitude-only VANS, standalone V4-C
recovery, a planner, waypoint selection, or a CBF-QP objective change. It would
be a fixed rule-table comparison among existing bounded modes. That comparison
requires callable and isolatable interfaces for every included productive mode.

## 3. Mode Semantics

M0 uses the documented CBF-QP `u_safe` action. M1 has an implemented bounded
wrapper-level slowdown helper. M2 is unavailable because the V4-C reports and
design notes remain but the associated runner, candidate generator, and
evaluator are absent from this Git worktree. M3 is interface-only: the robot
state contains velocity, and zero acceleration does not stop current motion.

The common H-step warning definition and diagnostic goal-distance-reduction
proxy are documented in existing work scripts. A common runtime comparison and
state-isolation check are nevertheless unavailable until the missing baseline
wrapper and M2 implementation are restored.

## 4. Fixed Selection Rule

No selector is implemented. A fixed selection rule must not be run when one of
its productive modes is unavailable. Implementing a rule that excludes M2, or
substituting a newly written recovery action, would test a different mechanism
and violate the preregistered R1 contract.

## 5. Results

No contexts were run. C003, C004, C002, C001, and C006 remain preregistered
but unobserved for this task. There are no M0 warning counts, M1 improvements,
M2 availability counts, M2 verified counts, productive opportunities,
progress-tradeoff measurements, state-isolation measurements, runtime
measurements, fail-safe opportunities, or active-smoke target.

| Item | Status |
| --- | --- |
| M0 normal mode | insufficient semantics in current worktree |
| M1 slowdown mode | implemented helper; not shadow-evaluable here |
| M2 V4-C recovery | unavailable |
| M3 safe halt | interface-only and excluded |
| Common horizon comparison | insufficient semantics |
| State isolation | not measurable |
| Formal executed command | not run and therefore unchanged by this task |
| Contexts completed | 0/5 |
| Active smoke eligible | false |

## 6. Interpretation

The stop is an interface limitation, not evidence against V4-C recovery or H7.
Safe halt is not treated as productive success. No recovery opportunity is
claimed, no shadow selection occurred, and no closed-loop effectiveness is
established. A barrier-function `h` would not be meter clearance, and a
goal-distance-reduction proxy would remain diagnostic rather than a
planner-quality metric.

## 7. Failure-Level Interpretation

Failure level: interface limitation. The current R1 mechanism has not been
tested, so it must not be labeled a mechanism failure. The current evidence
also does not support a simpler R4 decision because the same missing V4-C
interface blocks an executable trigger audit.

## 8. Decision

`r1_decision = inconclusive_due_to_interface_limitations`

Restore the exact V4-C wrapper-level recovery interface and the importable
official smoke wrapper, then repeat Stage 0 before any shadow or active test.

## 9. Claim Boundaries

- No active supervisor was run.
- No executed-command change occurred.
- No warning-reduction claim is made.
- No completion-improvement claim is made.
- No planner-improvement claim is made.
- This is not a benchmark or a statistical-significance result.
- No real-robot validation, global safety guarantee, or new CBF theorem is
  claimed.

R1 is restricted to shadow-mode scope if it is reopened. Any productive
supervisory-mode opportunity would be counterfactual evidence, not closed-loop
effectiveness. For this Stage 0 stop, no shadow opportunity was measured at all.
