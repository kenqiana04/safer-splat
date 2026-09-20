# Formal85 Attempt0 diagnosis

Attempt0 is immutable at `/disk1/zlab/v3_repair_records/post_repair_v3_bounded_recovery_paired_validation_v1_20260920`. `BATCH_STOP.json` records trial 66, exit code 1, and `CHILD_FAILURE_OR_MISSING_TRACE_LOCK`; `BATCH_COMPLETE.json`, `raw/trial_66`, and `runtime_trace_lock.json` are absent.

Exact traceback:

```text
Traceback (most recent call last):
  File ".../run_post_repair_v3_bounded_recovery_trial_v1.py", line 239, in <module>
    raise SystemExit(main())
  File ".../run_post_repair_v3_bounded_recovery_trial_v1.py", line 219, in main
    verify_child_authorization(args.one, root)
  File ".../run_post_repair_v3_bounded_recovery_trial_v1.py", line 68, in verify_child_authorization
    "protocol_sha256": sha(PROTOCOL), "execution_lock_sha256": sha(LOCK),
  File ".../run_post_repair_v3_bounded_recovery_trial_v1.py", line 32, in sha
    with path.open("rb") as stream:
FileNotFoundError: [Errno 2] No such file or directory: '.../POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_EXECUTION_LOCK.json'
```

The runner declared `POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_EXECUTION_LOCK.json`; the canonical on-disk lock and validator both use `POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_EXECUTION_LOCK.json`. The extra `VALIDATION_` is the entire defect.

Failure occurred inside `verify_child_authorization()` while hashing `LOCK`, before `delegate.run_one()`, runtime startup, any public cycle, PlantCommit, or Recovery evaluation. Root cause is `FORMAL85_ATTEMPT0_EXECUTION_HARNESS_LOCK_PATH_MISMATCH`, an execution-harness/pre-cycle infrastructure failure with no scientific result. Attempt0 must remain immutable because it is the authoritative failure record and cannot be continued, renamed, overwritten, or retroactively changed to PASS.
