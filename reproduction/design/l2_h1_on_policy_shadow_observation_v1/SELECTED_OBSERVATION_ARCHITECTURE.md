# Selected Observation Architecture

**Selected:** Option A, a post-commit in-process read-only tap feeding an out-of-process shadow worker.

```text
frozen controller computes and accepts u_k
  -> decision_commit_id becomes immutable
  -> copy x_k/u_k/dt/native candidates/map ref into immutable payload
  -> enqueue_nowait(bounded_queue)
  -> frozen controller applies the already-selected u_k

bounded_queue -> isolated L0/L1/L2 worker -> append-only result log
bounded_queue <- no controller reads
shadow result <- no controller reads
```

The capture occurs after `run.py:139-143` accepts the QP result and before `run.py:147` propagates the plant. The future hook may copy and enqueue only. It may not call L2, await a worker, mutate inputs, alter exceptions, or return a candidate.

The worker reconstructs immutable PR #84 `State` and `Control` objects, evaluates current-feasibility (L0), immediate segment (L1), and L2/H1 in that fixed order, and writes explicit reached/status/reason fields. This is a shadow observation pipeline, not the frozen controller's decision pipeline.

**Fallback:** Option B, an outer cycle wrapper/decorator, is permitted only if a future static interface exposes the identical commit ID, accepted `u_k`, native candidate set, stage reasons, and map reference without recomputation. If any are unavailable, the fallback fails closed and cannot collect formal data.

**Why not pure log scraping:** existing logs caused 4,259 missing controls and 5,795 unknown reachability records. Formal zero-code mutation is not evidence completeness.

**Scope:** DESIGN ONLY | NO ON-POLICY COLLECTION | NO CONTROLLER AUTHORITY | NO DECISION FEEDBACK | NO PERFORMANCE CLAIM.
