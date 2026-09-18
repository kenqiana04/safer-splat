# Implementation summary

Input authority: exact Gate 0 head `18ba8ed8aa3b4acc326426e05808bd5abe67561c`; F1 only, maximum six candidates, frozen order `+x,-x,+y,-y,+z,-z`. The new source has no global native-source privilege: C0 requires a matching `RecoverySourceGrant` tied to trial, cycle, state, map, actuator and transition identities. Existing C0 dimension, finite, state/map, lawful-source and actuator checks remain active.

`bounded_recovery.py` is proposal/exhaustion-only. `runtime_types.py` adds immutable typed facts. `supervisor.py` owns the exact reason allowlist, recovery-specific transition rows, source grant and final arbitration; its BYPASS method body is unchanged. `active_cycle.py` only sequences stages selected by Supervisor, prefetches current-state terminal evidence, reuses one L1 result and fresh per-candidate binding, and records attempt facts. `commit_transaction.py` adds those facts to the existing single ACTIVE trace append; it does not create a second plant or trace owner.

The old PR121 blob-lock unit test predated later authorized trace/plant/token changes. Its still-protected comparison now uses the exact Gate 0 parent blobs; no protected runtime blob is modified here. This is a regression test contract correction, not a runtime source change.
