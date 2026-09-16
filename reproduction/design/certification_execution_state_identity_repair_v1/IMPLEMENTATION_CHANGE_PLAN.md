# Implementation Change Plan

> Downstream implementation plan only. No implementation is performed by this specification task.

1. Add one pure canonical transition service and immutable arithmetic/state identity types under the V3 runtime implementation boundary.
2. Inject that same service into plant commit, L1, L2, normative dynamics projections, L3/backup witness construction, terminal certification, and segment certification.
3. Replace independent host-binary64 future-state expressions with `T_exec` or a bitwise-proven position projection.
4. Extend prepared bundle, retained token, cycle context, and trace evidence with canonical identities and typed match status.
5. Add fail-closed mismatch propagation without changing Supervisor priorities or candidate policy.
6. Add CPU/unit proofs, archived four-trial offline identity validation, and protected-source/policy-drift checks.
7. Freeze a new GPU smoke protocol only after implementation validation passes; do not reuse outcomes or tune geometry.

Implementation SHALL branch from `refreeze-active-runtime-v3-paired-execution-harness-after-trace-repair-v1@50cadfe614da70ce0345c4b1789c787dc529287e`, not from a diagnostic branch.
