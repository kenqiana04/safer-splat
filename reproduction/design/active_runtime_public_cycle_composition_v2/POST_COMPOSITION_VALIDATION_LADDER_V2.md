
# Post-composition validation ladder V2

1. Design public cycle composition (this task).
2. Implement `ActiveCycleCoordinator` and its typed API.
3. Revalidate active runtime contract conformance.
4. Only after full PASS, run `ACTIVE_RUNTIME_SMOKE_V2`.
5. Apply bug-only correction if needed.
6. Freeze engineering/final deadline/experiment/statistics protocol.
7. Run final active evaluation.

Design -> Implement -> Smoke is forbidden. No runtime implementation or smoke
is authorized by this document.
