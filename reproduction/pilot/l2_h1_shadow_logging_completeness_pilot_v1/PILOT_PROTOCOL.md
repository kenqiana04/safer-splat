# Frozen logging completeness pilot protocol

## Scope

- Upstream: PR #98 at `b47b0e924804e3e446b1f9c184ee5ea5d268d613`.
- Trials: official100 sorted positions 10, 30, 50, 70, 90; actual IDs 10, 30, 50, 70, 90.
- Matrix: five fresh, serial `WRAPPER_ON` runs; no OFF arm, repeat, replacement, or retry.
- Runtime: frozen Stonehenge environment, GPU 1, map, controller, dt, queue, schema, and L2/H1 observer.
- Data role: `PILOT_QA_ONLY`; never eligible for the formal prospective cohort.

## Independent denominator

`N_intended_steps` is reconstructed from the PR #98 committed-control trace. A trace step is intended only when it contains the selected control and the frozen plant invocation input/output for that same step. Capture JSONL never defines this denominator. A missing or malformed independent trace selects denominator Case C rather than silently shrinking the denominator.

## Completeness gates

For each run and overall, capture, selected numeric control, payload hash, map authority, reachability, terminal shadow result, and join completeness must equal 1.0. Queue drop, serialization error, worker exception/unavailable, alignment/schema/map failure, shutdown incomplete, sequence gap, duplicate payload, and duplicate result must all equal zero.

Legal certifier `L2_UNKNOWN` is counted descriptively and remains distinct from instrumentation-health failures. Shadow results retain zero controller, execution, candidate-selection, backup, terminal, or intervention authority.

## Fail-closed rule

Any invalid run or failed gate ends this task without another trial, implementation repair, threshold change, or result-conditioned replacement. Raw evidence remains on the server.
