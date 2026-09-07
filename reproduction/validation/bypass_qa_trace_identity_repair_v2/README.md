# Repair and Refreeze BYPASS QA Trace Identity V2

This task repairs one task-local metadata defect from PR #117 and freezes a fresh `BYPASS_EQUIVALENCE_PROTOCOL_V2R1`. It does not execute Stonehenge, use a GPU, enable ACTIVE mode, call a scientific oracle, or run official100.

The single identity authority is `canonical_trial_identity.py`. A native index such as `50` maps to `STONEHENGE_TRIAL_050` for both REFERENCE and BYPASS. The arm remains a separate `REFERENCE` or `BYPASS` field. The strict runtime `TRIAL_IDENTITY_MISMATCH` guard is unchanged.

PR #117 evidence remains historical and non-reusable. Only three PR #117 task-local QA plumbing files change: the shared arm adapter, serial manifest runner, and exact comparator. Production/runtime, controller, plant, geometry, deadline, backup, alternative, terminal, actuator, and oracle code are unchanged.

The V2R1 protocol has a new independent execution counter starting at zero, a hard cap of 10 arm executions, and no runtime correction quota. Its first pair must be fresh `REF50_new` and `BYPASS50_new`; this task creates templates only and does not activate the future execution lock.
