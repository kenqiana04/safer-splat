# REPORT — DESIGN CERTIFIED RECOVERY DEADLINE-AWARE ROUTING COMPLETION V1

## Answer first

- WARNING semantics: intentional fail-close when no valid retained backup exists; valid backup remains `ARB_BACKUP_GUARD`.
- EXPIRED semantics: intentional fail-close when no valid retained backup exists; valid backup remains `ARB_BACKUP_GUARD`; no late search.
- Overall classification: Case D, confidence HIGH.
- Root cause: explicit boundary coverage is missing for certified Recovery under non-open deadline with no valid retained backup.
- Proposed completion: `ARB_RECOVERY_WARNING_BOUNDARY` and `ARB_RECOVERY_EXPIRED_BOUNDARY`.
- Counterfactual: 27 WARNING and 7 EXPIRED unresolved lookups become explicit boundary routes; 0 Recovery actions, 0 plant outcomes, and 0 scientific values change.

## Evidence

The frozen boundary truth table contains 34 typed-valid rows. All have Recovery L3 PASS, selected count 0, and `ROUTING_RULE_MISSING`. The source audit shows `ARB_NAV` is OPEN-only, `ARB_BACKUP_GUARD` requires a valid retained backup, and the existing boundary guard excludes a certified candidate. This explains the missing route without treating deadline status as collision or certificate failure.

## Scope and next step

No runtime source, method logic, map, controller, candidate, deadline numeric profile, or scientific result was modified. The future implementation must add only supervisor-owned transition coverage, preserve backup precedence and no-action trace semantics, then pass active contract conformance before any smoke.
