# SAFC Level-2 No-Op Instrumentation Results

This directory contains compact outputs from a no-op closed-loop
instrumentation smoke validation of SAFC. The instrumentation logs SAFC states
and feedback candidates but does not modify nominal commands, CBF-QP outputs,
recovery actions, dynamics, planner outputs, or executed controls.

## Outputs

- `entrypoint_inventory.csv`
- `noop_equivalence_summary.csv`
- `state_transition_summary.csv`
- `feedback_candidate_summary.csv`
- `instrumentation_events_summary.csv`
- `metrics.json`
- `instrumentation_notes.md`

## Exclusions

No raw traces, full trial dumps, per-step dumps, active-constraint dumps,
trajectory samples, JSONL logs, or binary files should be committed here.
