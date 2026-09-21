# Routing Completion Truth Table

DESIGN ONLY — NO IMPLEMENTATION — NO GPU — NO FORMAL85 RERUN.

The frozen post-run boundary truth table contains **34** typed-valid final-cycle rows: **27 WARNING** and **7 EXPIRED**. All have a certified Recovery L3 PASS, no selected action, no Recovery PlantCommit, and `ROUTING_RULE_MISSING`. This table is used only to classify routing semantics and define a minimal completion rule.

| Context | Existing/required route | Action authority | Plant | Interpretation |
|---|---|---|---|---|
| Certified Recovery, deadline OPEN, no valid retained backup | Existing `ARB_NAV` | Supervisor-certified navigation | Allowed only through existing commit path | Timely navigation |
| Certified Recovery, WARNING/EXPIRED, valid retained backup | Existing `ARB_BACKUP_GUARD` | Retained backup | Existing backup path | Late navigation yields to backup |
| Certified Recovery, WARNING, no valid retained backup | New `ARB_RECOVERY_WARNING_BOUNDARY` | None / assurance boundary | No | Explicit fail-close boundary; no late Recovery selection |
| Certified Recovery, EXPIRED, no valid retained backup | New `ARB_RECOVERY_EXPIRED_BOUNDARY` | None / assurance boundary | No | Explicit fail-close boundary; no post-expiry search or commit |
| Recovery L2/L3 UNKNOWN, FAIL, exception, identity mismatch, or uncertified candidate | Existing typed block/fail-close routes | None unless a separately certified route exists | No implicit plant | Never admitted by the new rules |

The proposed rows replace an unresolved lookup with an explicit boundary result. They do **not** turn any of the 34 observations into a Recovery action and do not alter the frozen scientific result.

## Boundary IDs

`[74, 12, 73, 79, 54, 29, 0, 24, 98, 78, 82, 56, 21, 33, 44, 14, 61, 43, 47, 51, 42, 13, 49, 97, 53, 58, 34, 17, 62, 52, 22, 84, 57, 46]`
