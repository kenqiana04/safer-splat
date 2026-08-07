# REPORT: Core V1 representative-shortfall causal decomposition

## Result

`PASS_MULTIFACTOR_CORE_V1_SHORTFALL_DECOMPOSITION`

**Decision:** `DO_NOT_REOPEN_METHOD_OR_FREEZE_PAPER_UNTIL_ACTIONABLE_FACTORS_ARE_PRIORITIZED`  
**Unique next task (not started):** `RANK_CORE_V1_ACTIONABLE_FACTORS_AND_SELECT_ONE_BOUNDED_NEXT_STEP_V1`

This is Case D. It preserves the PR #87–#89 formal results and does not describe the 20-pair/Replica or source-map evidence as a new Core V1 result.

## Frozen scope

- Branch: `core-v1-representative-shortfall-causal-decomposition-v1`; base head: `047513b5e612f91e63ab1e7054815615cb455fd7`.
- Upstream formal record count: 1,440 method records on 360 states (E1=160, E5=100, E6=100).
- No training, rollout, controller loop, map change, registry change, or formal B0–B3 attempt occurred in this audit.
- C0/C1 were frozen before shadow execution: 16 E1 C0, 16 E5 C0 + 16 E5 C1, and 16 E6 C0 + 16 E6 C1.

## Key evidence

1. F11 found no implementation inconsistency: 768 method-level replay calls (two passes × 32 states × 4 methods × 3 environments) had zero semantic, candidate, or numerical mismatches. The position-first formulas had maximum absolute error `0.0e+00`.
2. F03 is a structural left-truncation fact: E5 had 100/100 and E6 74/100 B0 current-gate failures. Those states cannot show later B1/B2/B3 increment evidence under the frozen method chain.
3. F04 is a contributing timing constraint: the frozen dynamics prove `p_next=p+dt*v`, `v_next=v+dt*u`, `p(tau)=p+tau*v`, and `∂p(tau)/∂u=0` for the immediate interval. This does not make S2/S3 a replacement controller.
4. F05 does not isolate a B2 atomicity defect. All 32 Replica atomic witnesses passed; most selected E5/E6 cases were unreachable after current feasibility.
5. F06 cannot make a continuous-space or six-slot adequacy claim. Of 80 finite-set diagnostic states, 22 had primary B2 already committed and 58 were candidate-independently precluded by negative current-map `h`; no finite candidate needed current-gate evaluation.
6. F02/F07 retain genuine evidence limits: there is no frozen tracking-error budget, selected E5/E6 records have no official nonzero velocity, and the static assets contain no frozen on-policy/intermediate logs.
7. F09 keeps the map-evidence boundary: E1 carries frozen physical-reference evidence; E5/E6 remain behavior-only source-map environments.
8. F10 shows why zero events are not a low-rate exclusion: zero-event one-sided 95% upper bounds are 1.85% for E1 and 2.95% for E5/E6; E5/E6 B2 conditional denominators are 0 and 26, not 100.

## F01–F11 verdicts

| Factor | Verdict | Short reason |
|---|---|---|
| F01 | PARTIALLY_SUPPORTED | Formal records cover represented-map states but not frozen on-policy/deployment evidence; two source-map environments lack physical reference. |
| F02 | DATA_BLOCKED | Zero-velocity E5/E6 states cannot receive artificial velocity; no frozen tracking-error budget exists. Endpoint-only OAT shadows are not activation evidence. |
| F03 | STRUCTURAL_FACT | B0 left-truncated all E5 and 74/100 E6 states before B1/B2/B3; this establishes gating reachability, not a rescue. |
| F04 | SUPPORTED_CONTRIBUTING | The frozen position-first model exactly gives p(tau)=p+tau*v and dp(tau)/du=0 over the immediate interval; control first changes the next horizon. |
| F05 | NOT_SUPPORTED | All 32 Replica atomic witnesses passed; E5 and most E6 selected states were not reachable after the current gate. No isolated B2 atomic failure explains the zero increments. |
| F06 | NOT_IDENTIFIABLE | All 80 finite-set states were either B2-primary committed (22) or candidate-independently precluded by negative current-map h (58); no B3 coverage opportunity was reached. |
| F07 | DATA_BLOCKED | Static assets contain no frozen on-policy/intermediate logs; registry representativeness beyond its sampling contract cannot be established. |
| F08 | STRUCTURAL_FACT | Decision, certificate, availability, lead-time, backup-margin, and cost metrics separate quantities; all formal incremental action changes were zero. |
| F09 | PARTIALLY_SUPPORTED | Replica has frozen physical-reference evidence; Stonehenge/Flight are source Gaussian behavior-only and cannot sustain physical-clearance claims. |
| F10 | SUPPORTED_CONTRIBUTING | Zero events in 100/160 states leave nonzero 95% one-sided rates, and downstream E5/E6 denominators are 0/26 rather than 100. |
| F11 | NOT_SUPPORTED | All 768 double-replay method records matched frozen formal semantics; formula and protected-record checks passed. |

## Boundaries

- F02 endpoint shadows are configuration-exposure diagnostics only, not deployment claims.
- F06 is a finite pre-registered Grid7+Sobol512 set with frozen extras, not a continuous control-space proof.
- F08 certificate/availability quantities are not behavioral gains.
- E5/E6 have no physical-reference safety interpretation.
- The conclusion is multifactor; it neither reopens Core V1 expansion nor freezes an unsupported paper claim.
