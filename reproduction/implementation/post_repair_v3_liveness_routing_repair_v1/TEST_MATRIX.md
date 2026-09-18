# Deterministic CPU test matrix

`tests/test_bounded_local_recovery_v1.py` exposes individually named `test_T01`–`test_T48` methods. All are CPU fixtures, with synthetic plant transitions only.

| Tests | Implementation boundary |
| --- | --- |
| T01–T07 | F1 order, asymmetric endpoints, bound M, stable order, signed zero, primary dedup, no epsilon |
| T08–T09 | exact source grant and unchanged C0 actuator gate |
| T10–T16 | primary/backup priority and exact entry suppression/allowance |
| T17–T22 | first/second PASS, exhaustion, UNKNOWN, terminal/boundary, source rejection |
| T23–T29 | same-key no-retry, PAUSED cursor, key identities/version, trial isolation |
| T30–T35 | retained backup, final Supervisor selection, deadline, state and transition binding |
| T36–T39 | one-ULP distinction, sampled-data causality, diagnostic shell nonauthority |
| T40–T48 | attempt trace/order, trace failure, bounded scan, next cycle, key change, ownership, exact-one, sole plant |

Adapted Gate 0 E01–E16 exercise the actual provider/key/register; R01–R24 exercise the public Coordinator/Supervisor with deterministic CPU backends. The existing Active Runtime package and V3 geometry regression suites are rerun. No scientific outcome is computed.
