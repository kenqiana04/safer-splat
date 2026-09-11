## Mechanical import only

This Draft PR mechanically imports the supplied `FORMAL_V2_EXECUTION_BUNDLE` from `/home/zlab/control` into `reproduction/formal/active_runtime_paired_experiment_v2/`.

The imported 12 files are authoritative and were copied without protocol, manifest, statistical-plan, runtime, controller, map, geometry, deadline, oracle, or parameter edits. Only two task-local files were added: `IMPORT_VALIDATION.json` and this PR body.

Validation completed:

- PR #138 exact identity: `606edd1c254f4ffaec48e0b84d8f5e5f29c039ec`
- Both Python files pass `python -m py_compile`.
- All supplied JSON files parse.
- The manifest has 100 unique trial IDs `0..99`, with 85 `PRIMARY_FORMAL` and 15 `DEVELOPMENT_EXPOSED_SECONDARY`; the cohorts are disjoint and the frozen execution ranks are unique `1..100`.
- `bash -n start_formal_v2_tmux.sh` passes both on the local Git Bash and on the source host.
- `FORMAL_PROTOCOL_FILE_HASHES_V2.json` and `BUNDLE_SHA256.json` both match every imported file.
- Relative to PR #138, runtime, production, and frozen-method source diffs are zero.

No formal Reference arm, Active arm, Pilot, Smoke, 96-scenario suite, BYPASS, GPU computation, oracle, or parameter tuning was run. Formal scientific arm count is exactly zero.

`FINAL_STATUS=PASS_MECHANICALLY_IMPORT_FORMAL_PAIRED_EXPERIMENT_V2`

`FINAL_DECISION=READY_FOR_FORMAL_COLLECTION_PREFLIGHT_V2`

Only next task: `START_FORMAL_PAIRED_COLLECTION_V2`
