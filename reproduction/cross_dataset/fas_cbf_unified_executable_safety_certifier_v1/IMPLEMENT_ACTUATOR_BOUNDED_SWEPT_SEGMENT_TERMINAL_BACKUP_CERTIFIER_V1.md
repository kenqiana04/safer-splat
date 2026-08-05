# Implement Actuator-Bounded Swept-Segment Terminal-Backup Certifier V1

This task implements the first candidate-level executable-safety certifier under
the frozen FAS-CBF Core V1 contract from PR #83.  It is deliberately bounded to
the task-owned directory containing this file.

The normative dynamics are
`POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`:

```text
p_next = p + dt * v
v_next = v + dt * u
p(tau) = p + tau * v, tau in [0, dt]
```

A control may be committed only after actuator admissibility, current full-map
feasibility, continuous swept-segment certification, and a finite terminal
backup witness all pass. Unknown/nonfinite map evidence, budget exhaustion, or
candidate-library exhaustion never imply mathematical unrecoverability.  The
implementation never consumes an offline reference oracle online, never trains
or mutates a map, and does not claim deployment safety, global recursive
feasibility, an exact continuous-control `U_exec`, or full-stack superiority to
SAFER.

The protocol decision tree, required counters, protected-source boundary, PR
lineage, map-smoke limitations, proof-status vocabulary, and final reporting
contract are those supplied in the user-authorized task
`IMPLEMENT_ACTUATOR_BOUNDED_SWEPT_SEGMENT_TERMINAL_BACKUP_CERTIFIER_V1` on
2026-08-05.
