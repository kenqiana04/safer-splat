# Primary Proposal Integration V2

The existing PD calculation in `run.py:118-127` produces `u_des`, a desired reference only. The existing `CBF.solve_QP` / Clarabel result at `run.py:132` is the sole native primary proposal and is typed `PRIMARY_NATIVE_CBF_QP`. Neither object has selection or commit authority.

The current Clarabel problem has CBF half-space constraints but no componentwise actuator box. A successful finite QP result is therefore passed unchanged to C0. C0 checks the exact candidate against the PR #109 inclusive `[-0.1,0.1]^3` authority. Out-of-box means `C0_FAIL_LOCAL/F_ACTUATOR_ADMISSIBILITY_LOCAL`; it is rejected without clipping. Any value-changing transform creates a new identity and requires full recertification, but no such transform is authorized here.

The current legacy `solve_QP` returns `u_des` when the solver fails. The V2 proposal adapter must use the solver status and emit `NO_PRIMARY_PROPOSAL`; it must never expose that legacy return value as a proposal or fallback.
