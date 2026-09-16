# Cert-exec identity smoke launcher guards R2

`PASS_CERT_EXEC_IDENTITY_SMOKE_LAUNCHER_GUARDS_R2`

The R2 launcher now targets only the R2 worktree and branch, requires the
locked old failed root to exist with an exact immutable manifest, and requires
the retry1 result root to be absent. `--prelaunch-check-only` performs only
read-only guards, CPU static preflight, and validator checks; it creates no
directory, tmux session, GPU process, trial, controller/QP call, or PlantCommit.

The base-config plumbing repair from c19ffc is preserved. The frozen protocol,
historical V3 base config, geometry, cohort `[15,45,75]`, 500-cycle limit, and
scientific decision remain unchanged. CPU syntax, shell syntax, fixture
regressions, static preflight, prelaunch check, validator, and diff checks pass.
No GPU or smoke execution was performed in R2.
