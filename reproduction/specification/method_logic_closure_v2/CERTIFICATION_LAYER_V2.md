# Safety Certification Layer V2

The certification layer is pure evidence production. It never commits an action.

1. **I0a — INITIAL_START_ADMISSION.** Used only for initial activation or explicit reset/re-entry. It returns typed admission evidence.
2. **I0b — INITIAL_OR_REENTRY_REPAIR_CERTIFICATION.** A projection or repair may propose a changed initialization state only when that state may lawfully be changed. Full re-certification is mandatory. Runtime state projection is forbidden.
3. **R0 — RUNTIME_CURRENT_STATE_ROLE.** Target role: `CHEAP_DIAGNOSTIC_OR_HEALTH_PRECHECK_ONLY`. Under one geometry predicate, a formal closed L1 certificate over `[p_k,p_(k+1)]` includes `p_k`; therefore L1 PASS implies current-point PASS. I0a/I0b remain independent.
4. **L1 — IMMEDIATE_CANDIDATE_INDEPENDENT_SEGMENT.** Certifies closed `Segment(p_k,p_(k+1))`; total result is PASS, FAIL, or UNKNOWN with reason scope. FAIL is not an alternative-search opportunity.
5. **P0 — PRIMARY_PROPOSAL_INTERFACE.** A nominal reference is not a control candidate. The controller produces `PRIMARY_PROPOSED_CONTROL`; no proposal has execution authority.
6. **C0 — CANDIDATE_ADMISSIBILITY.** Checks finite values, dimensions/types, provenance, actuator authority, state/action/time alignment, source legality, identity, and candidate-specific feasibility. Total result: PASS, FAIL_CANDIDATE_LOCAL, UNKNOWN_GLOBAL_OR_AUTHORITY, or evidence-backed UNKNOWN_CANDIDATE_LOCAL_COMPUTE.
7. **L2 — FIRST_CONTROL_SENSITIVE_SEGMENT.** Certifies H1 `Segment(p_(k+1),p_(k+2)(u_k))` as PASS, FAIL, or UNKNOWN(reason scope). PASS is not recoverability; FAIL is not global impossibility.
8. **L3 — BACKUP_VIABILITY / RECOVERABILITY_WITNESS.** Entered only after C0 PASS and L2 PASS. Total result: WITNESS_FOUND, WITNESS_ABSENT, or UNKNOWN(reason scope). It proves only a sufficient witness under the frozen contract.

All results are immutable inputs to the supervisor. Shadow-mode results are not inputs at all: they are post-commit observations with zero authority.
