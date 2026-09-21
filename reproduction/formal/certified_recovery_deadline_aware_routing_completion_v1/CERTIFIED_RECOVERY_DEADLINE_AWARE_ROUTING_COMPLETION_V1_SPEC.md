# Certified Recovery Deadline-Aware Routing Completion V1

**DESIGN ONLY — NO IMPLEMENTATION — NO GPU — NO FORMAL85 RERUN.**

## Objective

Complete the runtime routing coverage for a certified bounded-local-Recovery candidate that reaches arbitration after its deadline becomes WARNING or EXPIRED, without granting that candidate late selection authority. The design preserves the already observed fail-close semantics and makes the boundary route explicit and auditable.

## Rule names and exact predicates

Add two mutually exclusive future routing rows to the supervisor-owned transition authority:

- `ARB_RECOVERY_WARNING_BOUNDARY`: source phase `ARBITRATION`, event `ARBITRATE`, candidate source `SOURCE_BOUNDED_LOCAL_RECOVERY_V1`, candidate fact certified (`L3 PASS`, prepared bundle present, candidate identity matches), `deadline.status == WARNING`, `retained_backup_valid == false`, terminal not eligible, and no higher-priority route is applicable. Destination is `ASSURANCE_BOUNDARY`; `commit_allowed=false`; `may_start_new_search=false`; `action_authority=NONE`; failure mapping is `DEADLINE_INADMISSIBLE_NO_VALID_BACKUP`.
- `ARB_RECOVERY_EXPIRED_BOUNDARY`: the same factual predicate with `deadline.status == EXPIRED`. It additionally records that no post-expiry search or candidate generation is allowed. Destination and commit fields are identical.

The future implementation must use factual context fields, not a synthetic hint or a coordinator-side policy branch. `certified` means the existing L3/identity/prepared-bundle facts already consumed by `Supervisor.arbitrate`; it does not recompute L2/L3.

## Priority and fail-close

The existing priority remains unchanged: timely certified navigation first; a valid retained backup outranks a late navigation candidate; eligible certified terminal remains available only through the existing terminal route; otherwise the assurance boundary is returned. The new rows are only reachable after the backup guard has failed because no valid retained backup exists. They never select Recovery, terminal, nominal, desired, hold-last, zero, or an uncertified action.

For WARNING, a valid retained backup continues to resolve `ARB_BACKUP_GUARD`; no valid backup resolves the explicit Recovery boundary row. For EXPIRED, the same backup precedence applies, while new search and new backup discovery remain prohibited. OPEN behavior is unchanged and continues to resolve `ARB_NAV` when the existing certified-navigation facts hold.

## Unknown and failure semantics

L2/L3 UNKNOWN, exceptions, identity mismatch, missing prepared bundle, or non-certified candidates do not satisfy the new predicates. They retain their existing typed block/fail-close behavior. The new rows are not a conversion of UNKNOWN to PASS and do not create a fallback action.

## Scientific boundary

This is routing-completeness design only. It changes no map, geometry, controller, candidate family, deadline numeric profile, certification result, plant outcome, progress value, NI result, or efficacy interpretation. The 34 historical rows remain boundary observations; their prior scientific result is immutable.
