# Internal Logs And Commands Status

## Scope

The following files are internal task / run records:

- `work/risk_aware_cbf/notes/commands.txt`
- `work/risk_aware_cbf/notes/run_mpc_style_recovery_h2_n64.log`
- `work/risk_aware_cbf/notes/run_mpc_style_recovery_h2_n64_detached.log`
- `work/risk_aware_cbf/notes/run_mpc_style_recovery_h2_n64_resumable.log`
- `work/risk_aware_cbf/notes/run_mpc_style_recovery_h3_n64_detached.log`
- `work/risk_aware_cbf/notes/run_mpc_style_recovery_resume_smoke.log`

## Recommendation

These files can be retained as reproduction-side internal notes, but they should not be placed in `paper_materials/` and should not be cited directly in the paper.

If the repository is later prepared for a commit, decide explicitly whether to:

- keep them as tracked internal notes,
- move command snippets into a curated reproduction README,
- or add run logs to ignore rules.

Do not delete them as part of the current freeze decision task.

## Current Handling

No run logs were deleted in this task. They remain internal records of the MPC-style targeted pilot and detached reruns.
