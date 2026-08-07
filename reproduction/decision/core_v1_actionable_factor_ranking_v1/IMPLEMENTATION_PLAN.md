# Implementation plan: Core V1 actionable-factor ranking

## Scope lock

This task is a desk-based decision analysis only. It reads frozen PR #84–#90 evidence and creates no Core V1 implementation, no controller change, no map/data change, no B0–B3 run, and no representative cohort.

## Execution steps

1. Freeze the live identity of PR #84–#90 and verify the protected PR #90 source bytes against their Git objects.
2. Materialize the pre-frozen A1–A5 registry, dependency graph, fatal-dependency audit, scoring contract, effort estimates, and role-separated reviews from the frozen evidence.
3. Apply the arithmetic and fatal/dependency rules. Produce exactly one selected case and exactly one downstream task contract.
4. Run the repository validator, tests, compile check, Git whitespace check, and a read-only GPU/process/operational preservation check.
5. Copy only the final `REPORT*.md` to the report handoff location, commit only this task directory, push, and open one Draft PR based on PR #90.

## Stop rule

Stop after the selected next task is documented. The selected task is not executed here.
