# SAFC Level-1 Offline Reconstruction Results

This directory contains compact outputs from a report/log-level offline
reconstruction of the SAFC state machine. The reconstruction uses existing
tracked reports and optional compact local metrics when available. It does not
run new closed-loop experiments, does not modify the controller, and does not
claim performance improvement.

## Outputs

- `source_inventory.csv`: designated evidence sources, availability, use, and
  scope.
- `event_inventory.csv`: report-level aggregate events mapped to SAFC states
  and bounded feedback actions.
- `state_transition_summary.csv`: grouped reconstructed state transitions.
- `feedback_action_summary.csv`: grouped feedback actions and claim scopes.
- `metrics.json`: compact Level-1 counts and fixed claim limitations.
- `reconstruction_notes.md`: source policy, mapping rules, claim boundaries,
  and limitations.

## Exclusions

No raw traces, per-step dumps, full `trials.csv`, active-constraint dumps,
trajectory samples, or JSONL traces should be committed here.
