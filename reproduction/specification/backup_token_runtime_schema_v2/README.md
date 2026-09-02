# Backup Token Runtime Schema V2

This directory freezes a schema-only bridge from an L3 backup witness to a content-addressed immutable certificate bundle and a separately mutable Supervisor-held token handle. It implements no runtime token, supervisor, backup controller, candidate generator, terminal policy, or experiment.

The central separation is:

1. L3 witness: certification fact.
2. Immutable bundle: content-addressed evidence and certified tail.
3. Retained token: runtime handle referencing one bundle.
4. Runtime state: cursor, revision, and VALID/INVALID/EXHAUSTED consumption state.

Only the frozen no-error simulation theorem is covered. Physical tracking error, delay, disturbance, emergency action, and terminal priority remain outside this contract.
