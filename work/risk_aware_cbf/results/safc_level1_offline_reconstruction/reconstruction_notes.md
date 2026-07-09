# SAFC Level-1 Reconstruction Notes

## Scope

This is Level-1 offline reconstruction. It validates whether existing reports
can be consistently mapped into the SAFC state machine. It does not run new
experiments, does not modify control, and does not claim SAFC performance
improvement.

## Source Policy

The default run reads only the designated `REPORT*.md` files. Optional local
inputs are limited to compact `summary`, `metrics`, or `inventory` CSV/JSON
files smaller than 5 MiB. The reconstruction does not read raw traces,
`trials.csv`, per-step dumps, active-constraint dumps, trajectory samples, or
JSONL files.

## Mapping Rules

1. **Start-Safe / repair:** explicit certification, successful repair, or
   full-query verification maps S0 Pre-Execution Certification to S1 Nominal
   Filtering with `admit_task`. Unresolved repair maps to a halt or replan
   candidate only when directly supported.
2. **CBF-QP:** zero aggregate infeasibility maps S1 to S2 with `no_feedback`.
   Positive infeasibility maps to S4 only when recovery availability is
   explicit; otherwise it maps conservatively to an S6 halt candidate.
3. **DT Verification:** positive H1/H2/H3 or aggregate horizon-margin counts map
   S2 to S3. The feedback is a slowdown candidate unless the same named
   evidence explicitly activates recovery.
4. **Triggered Recovery:** named V4-C use maps S3 to S4; named success with
   post-recovery margin resolution maps S4 to S2. Recovery failure maps S4 to
   an S6 halt candidate.
5. **Collision / stop:** positive collision evidence maps the active execution
   context to an S6 halt candidate. FC-Aware fixed/capped collision evidence is
   diagnostic and does not assign causality to the cap.
6. **Replan candidate:** repeated warning, unresolved recovery, recovery-disabled
   collision, or repeated DT risk may map S3/S4 to S5 with
   `replan_request_candidate`. This is an interface-level reconstruction, not
   an implemented planner.

## Claim Boundaries

- DT warning is not collision.
- QP infeasibility is not collision.
- Recovery success is configuration-specific.
- Replan request is interface-level.
- Risk-cost update is future planner integration unless separately implemented.
- Safe halt is a conservative fallback, not global safety proof.

## Limitations

- Report-level aggregate evidence only.
- Not per-step state reconstruction unless compact per-event summaries exist.
- Missing scripts/results remain release gaps.
- No new controller behavior.
- No performance improvement claim.
- No planner validation.
- No real-robot validation.
- Event counts reflect reconstructed evidence rows, not independent trials or
  causal effects.
