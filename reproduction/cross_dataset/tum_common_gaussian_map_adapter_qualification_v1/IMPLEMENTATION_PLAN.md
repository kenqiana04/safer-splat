# TUM Common Gaussian Map Adapter Qualification V1 Implementation Plan

> **For agentic workers:** execute the frozen qualification protocol in this isolated worktree only.

**Goal:** Prove or fail closed on lossless, method-specific canonical Gaussian adapters for the frozen TUM SplaTAM and Gaussian-SLAM maps, then run the already-approved static-only audit only for verified adapters.

**Architecture:** Server-side scripts perform read-only source and map identity audits, deterministic task-owned canonical exports, semantic parity gates, and compact summaries. The tracked directory contains scripts, compact manifests, validation, and a report; large maps, arrays, renders, caches, and logs remain on the server.

**Tech Stack:** Python, NumPy, PyTorch, official SplaTAM/Gaussian-SLAM source archives, existing SAFER static-audit semantics, SSH, GitHub Draft PR.

---

- [ ] Reconfirm PR #39 identity and create the isolated branch/worktree.
- [ ] Freeze external source, dataset, query, and map identities without modifying any input.
- [ ] Audit parameter and coordinate semantics from the exact official source snapshots.
- [ ] Build deterministic, lossless canonical exports and verify round-trip, covariance, coordinate, and native renderer parity per method.
- [ ] Only for a verified adapter, run static-only SAFER map/query/gradient/continuity checks and classify G0.
- [ ] Recheck all input hashes and process boundaries; validate compact artifacts and report.
- [ ] Commit only the task directory, push, and open a Draft PR based on PR #39.
