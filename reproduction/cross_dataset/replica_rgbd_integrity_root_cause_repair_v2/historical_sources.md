# Historical source recovery ledger

The authority is commit `fe250df543aa158557c176ee4f87dc131bb61e60` on the
non-ancestor frozen-render branch. The exact source byte identities and their
task use are recorded in `historical_replica_source_identity.json`. This task
does not cherry-pick that branch; `replica_v2_pipeline.py` is a task-owned
implementation with explicit provenance and the recovered V1 checker rule.
