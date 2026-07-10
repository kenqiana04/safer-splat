# VANS Shadow Feasibility Audit Notes

## Scope

This is a shadow-only counterfactual feasibility audit. It does not execute a
shadow-selected candidate and does not modify the formal trajectory.

## Candidate Set

Only N0/N1/N2 are enabled because directional action semantics are not
grounded as planar heading commands.

## Decision

`vans_decision = retain_as_diagnostic_extension`

Verification-Aware Nominal Action Selection has not yet been actively
validated. Shadow opportunities, if present, are counterfactual one-state/H-step
observations only.
