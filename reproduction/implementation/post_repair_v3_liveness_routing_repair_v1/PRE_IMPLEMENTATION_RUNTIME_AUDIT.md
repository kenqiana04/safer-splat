# Pre-implementation runtime impact audit

Exact source baseline: Gate 0 HEAD `18ba8ed8aa3b4acc326426e05808bd5abe67561c`. This audit was performed before shared runtime edits.

| Authority / lifecycle | Actual source and current behavior | Needed additive seam |
|---|---|---|
| Candidate/source/identity | `runtime_types.py:266-303`; `make_candidate` hashes vector/role/provenance and allows only `PRIMARY_NATIVE_CBF_QP` or `SOURCE_NATIVE_EXISTING`; snapshot identity includes cycle index and goal. | Distinct recovery provenance and bit-exact vector dedup, without changing existing IDs. |
| C0 | `c0_admission.py:13-23` checks dimensions, finite, exact state/map provenance, lawful source and componentwise bounds; no clipping. | Recovery-specific admission requiring a typed Supervisor grant; preserve all existing checks. |
| L1/L2/L3 | `l1_runtime.py` caches candidate-independent same-cycle immediate closed segment and binds each attempt; `l2_runtime.py` computes p(k+1), p(k+2) from candidate; `l3_runtime.py` and repaired `repaired_components.py` produce status/reason/prepared bundle using canonical witness. | Same L1 result, fresh binding/C0/L2/L3 per recovery vector; typed L3 FAIL scope carrier. |
| Route/selection | `supervisor.py:86-314` resolves 44 frozen rows exactly once; `:314` route API and `:418-447` final nav>backup>terminal>boundary arbitration. | Versioned disjoint recovery rows through Supervisor only; candidate-local typed trigger and backup priority. Historical 44 rows unchanged. |
| Coordinator/session | `active_cycle.py:66-110,345-760` owns trial session and stage sequencing; L3 FAIL currently routes to arbitration, terminal runs after arbitration, native alternative provider only behind existing route. | Inject recovery source/register, current-state terminal prefetch, finite ordered scan and typed facts; never select executable action itself. |
| Native alternatives | `alternative_provider.py` accepts only pre-existing `SOURCE_NATIVE_EXISTING`; real stack wires empty provider. | Do not relabel or mutate native provider. |
| Backup/terminal | `backup_token_store.py` validates exact state/map/geometry/actuator/dynamics and cursor; `terminal_runtime.py` requires fallback context and certified zero hold. | Read validation facts only; cached terminal result exact snapshot; no token/terminal policy change. |
| Deadline | `deadline_runtime.py` observes OPEN/WARNING/EXPIRED; Supervisor interprets guards. | Observe before search and commit; no coordinator deadline policy. |
| Trace/plant | `commit_transaction.py` owns ACTIVE plant→token→single trace outcome; `trace_writer.py` appends/finalizes, `PlantCommitAdapter.commit` is sole execution. | Add recovery normative facts to existing one-cycle ACTIVE record, without pre-commit append or duplicate outcome; missing evidence ineligible. BYPASS path uses separate `ActiveRunner.commit_bypass`. |
| Canonical transition and state binding | `certification_execution_state_identity_repair_v1/canonical_transition.py` and repaired L3 stack bind float32 transition/evidence; V3 projection owns hard 0.015 q geometry. | Reuse unchanged; no change to radius, map, dynamics, comparator, certificate mathematics. |

The source does not yet carry a recovery authority, exact numeric-state exhaustion register, typed per-attempt L3 FAIL in final trace, or recovery transition rows. These are implementation gaps, not licenses to alter Gate 0 design.
