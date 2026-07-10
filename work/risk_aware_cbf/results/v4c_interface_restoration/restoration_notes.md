# Restoration Notes

## Search Scope

Read-only searches covered the 4090 `/disk1/zlab` and `/home/zlab` trees, local
Documents/Desktop/Downloads roots, all local Git refs and worktrees, Git named
objects, and unreachable objects. The first remote search had a shell quoting
error and produced no candidate list; the corrected read-only search found the
original runner, sweep, analysis, wrapper, and its original V1/V4-B helpers in
`/disk1/zlab/projects/safer-splat`.

## Accepted Sources

The 4090 worktree at `master` commit
`57c55485e357343c3d166a9123ab9a9275c12067` is the Priority-1 source. Its four
artifact hashes exactly match the restored files. Dated July 2 and July 3 local
archives independently match the same script hashes and include reports and
the Flight100 original command log. The `generated_remote_v4c` copies have the
same hashes but weaker directory provenance, so they were not used as the
selected source.

## Restoration Boundary

Only the three named V4-C scripts and the official smoke wrapper were copied.
No raw `trials.csv`, debug trace, JSONL, trajectory sample, active-constraint
file, image, checkpoint, model, or binary was restored. The V4-C source bytes
were not edited, refactored, or retuned.

## Importability Boundary

`py_compile` passes locally using an external pycache directory. The local
default Python lacks `torch`, so local CLI help cannot test dependencies. In
the original 4090 `safer_splat_official` environment, both original files
import and `--help` exits successfully without running an experiment. The
current Git branch still lacks the original V1/V4-B helper imports required by
the V4-C runner. An adapter cannot remove that dependency without crossing the
restoration boundary, so none was created and no equivalence check was run.

## R1 Reopening Result

M0 and M1 artifacts are restored and semantically auditable. M2 is restored
with confirmed provenance but remains unavailable as a callable evaluator in
this Git branch. M3 remains interface-only. R1 Stage 0 is therefore not rerun,
and the preregistered R1 shadow audit remains blocked.
