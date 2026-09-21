# Routing Completion Proof Obligations

**DESIGN ONLY — NO IMPLEMENTATION — NO GPU.**

1. **Deadline ownership:** only `DeadlineTracker.observe` produces the status; only `Supervisor` interprets it.
2. **Certified fact:** each new rule requires existing L3 PASS, prepared-bundle presence, and candidate identity equality.
3. **Recovery provenance:** each new rule requires `SOURCE_BOUNDED_LOCAL_RECOVERY_V1`; primary and alternative candidates cannot match.
4. **Backup precedence:** any valid retained backup must match `ARB_BACKUP_GUARD` first; the new boundary rows require backup invalid/absent.
5. **Deadline partition:** WARNING and EXPIRED are separate exact predicates; OPEN cannot match either.
6. **No action:** both rows have `commit_allowed=false`, no action authority, and destination `ASSURANCE_BOUNDARY`.
7. **No new search:** neither row permits candidate generation, alternative search, backup discovery, terminal evaluation, or post-expiry work.
8. **Unknown/failure exclusion:** UNKNOWN, FAIL, exception, identity mismatch, and missing evidence do not satisfy the certified predicate.
9. **Trace/plant invariant:** boundary uses the existing no-action trace path exactly once and invokes no plant commit.
10. **Scientific noninterference:** no map, geometry, controller, candidate values, certification thresholds, deadline numbers, or scientific analysis artifacts change.
11. **Mutual exclusion:** the two new rows are disjoint by exact deadline status and disjoint from all existing navigation/backup/terminal guards.
12. **Termination:** every legal context resolves to existing commit/backup/terminal behavior or a typed assurance boundary; zero/multiple matches remain typed routing blocks.
