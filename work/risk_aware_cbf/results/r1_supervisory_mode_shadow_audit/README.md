# R1 Supervisory Mode Shadow Audit

## Status

Stopped at Stage 0 semantics and interface audit. No shadow evaluation was
run, no formal trajectory was executed, and no active supervisor was run.

The current worktree lacks both the importable official smoke wrapper used by
the existing SAFC/VANS runners and the callable V4-C recovery implementation.
M2 cannot be generated or evaluated from isolated cloned state without
substituting a recovery action, which is forbidden by the R1 task.

Only the preregistration table is included in this directory. It excludes all
modes from execution because the common-comparison gate did not pass. There are
no per-step artifacts, raw traces, trial tables, JSONL files, images, models,
or binary outputs.

## Decision Boundary

This is an inconclusive interface result, not a negative V4-C result and not a
closed-loop R1 result. Restore the missing wrapper and recovery interface before
reopening the shadow audit.
