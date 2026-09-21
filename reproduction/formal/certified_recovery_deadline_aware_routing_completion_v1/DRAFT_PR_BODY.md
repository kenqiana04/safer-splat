## Design-only routing completion

This Draft PR diagnoses the frozen Formal85 Retry3 `ROUTING_RULE_MISSING` boundary rows and freezes a minimal additive design. It does not modify runtime code, run GPU, rerun Formal85, or alter the scientific result.

- WARNING: 27 rows; EXPIRED: 7 rows.
- Existing `ARB_NAV` remains OPEN-only.
- Existing `ARB_BACKUP_GUARD` remains the higher-priority route when a valid retained backup exists.
- New future rule IDs: `ARB_RECOVERY_WARNING_BOUNDARY` and `ARB_RECOVERY_EXPIRED_BOUNDARY`. Both are no-action assurance-boundary routes with `commit_allowed=false`.
- UNKNOWN/FAIL/identity-mismatch candidates cannot match.
- Counterfactual changes: 0 Recovery actions, 0 plant outcomes, 0 scientific values.

Only next task: implement the additive supervisor-owned routing completion, then revalidate active runtime contract conformance.
