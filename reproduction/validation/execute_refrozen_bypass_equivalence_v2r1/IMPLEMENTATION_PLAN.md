# Execution plan

1. Verify PR #118, protocol, repair validation, protected source, GPU, environment, and Stonehenge artifacts.
2. Freeze the task-local harness, exact comparator, validator, ledger schema, input lock, execution lock, and Q0R1 result; commit and push before any real arm.
3. Execute fresh pairs serially in order 50, 10, 30, 70, 90. For each pair run REFERENCE then BYPASS in fresh processes, append the immutable ledger, compare exactly, and stop without retry on the first failure.
4. Freeze compact/raw task-owned QA evidence, validate, review, report, commit, push, and open one Draft PR. Do not run ACTIVE, an oracle, smoke, or official100.

