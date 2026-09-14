# Active Runtime V3 Paired Validation Execution Harness

This directory freezes the pre-outcome execution harness for the 85-trial Active Runtime V3 arm. It is based on PR #144 head `0ef0523050fc8e6c77fe333709477c5a4161d489` and the pre-outcome protocol SHA-256 `2de32310c84db49f0b8982e2bb63f15d234732250a5c3ddf859fdb75386439c5`.

The harness delegates runtime construction and execution to the existing Pilot/Smoke V3 path and PR #140 wiring. Its task-local observation wrapper records already-produced state/action runtime facts without modifying inputs, outputs, routing, certification, plant commits, or the `0.015 q` authority. Resume skips only evidence that is complete, finalized, hash-locked, trace-cardinality exact, GPU-released, and integrity-clean.

Static preflight and validation are CPU-only. This freeze performed no Active V3 arm, Reference rerun, oracle, Official100, or new Formal outcome. The launcher deliberately stops after collection for human review and never starts the analyzer.

`FINAL_STATUS=PASS_ACTIVE_RUNTIME_V3_PAIRED_EXECUTION_HARNESS_FREEZE`

`FINAL_DECISION=READY_FOR_MANUAL_ACTIVE_RUNTIME_V3_PAIRED_COLLECTION`

`ONLY_NEXT_TASK=MANUALLY_START_FROZEN_ACTIVE_RUNTIME_V3_PAIRED_COLLECTION`
