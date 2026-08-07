# Core causal role state machine specification

The state machine is a specification, not code. It has 15 semantically distinct states: S0 unassessed; S1 start-admissible; S2 repair-required; S3 repair-failed; S4 immediate-segment-safe; S5 immediate-unsafe-unavoidable; S6 primary-under-test; S7 primary-future-safe; S8 primary-recoverable; S9 primary-not-certified; S10 alternative-search-eligible; S11 alternative-certified; S12 terminal-certified; S13 fail-closed; S14 commit.

All terminal execution/fail-close states return only to a new-cycle diagnostic state. No transition equates fail-close with safe stop, and no transition opens alternative search for a start-infeasible or immediate-unavoidable state.
