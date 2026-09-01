# L2/H1 Primary Reachability Diagnosis V1

This task performs one post-hoc, read-only diagnosis of why the frozen formal cohort has `N_primary=0`. It does not change PR #102 evidence, rerun trials or bootstrap, use GPU, recompute scientific prevalence, or modify runtime code.

The frozen G1–G10 funnel shows 14,122 rows surviving G1–G5 and zero surviving G6 (`l1_status=PASS`). Every row has `l1_status=NOT_REACHED`, `l2_reached=false`, and compact reachability reason `L0_BLOCKED`. The frozen adapter source confirms that any non-PASS L0 result writes exactly these values before calling L1 or L2.

Therefore the root class is `D1_L1_ZERO_PASS_SUPPORT`, with subcause `UPSTREAM_L0_BLOCKED_BEFORE_L1_CERTIFIER_EXECUTION`. This does not reinterpret Case C and does not establish an L1 or L2 safety outcome.

The canonical table was streamed once on the server. Four compact CSVs were written before a server-Python JSON serialization wrapper incompatibility occurred; the remaining JSON summaries were recovered only from those compact files, without rereading or copying the canonical table. See `STREAMING_PACKAGING_RECOVERY_RECORD.json`.
