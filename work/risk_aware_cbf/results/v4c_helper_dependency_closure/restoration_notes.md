# Restoration Notes

- Restored exactly two direct helper files; no additional transitive local
  Python file was needed.
- Both target SHA256 values match the Priority-1 source and corroborating local
  copies. The helpers were untracked in the Priority-1 worktree, which is
  disclosed rather than represented as Git provenance.
- Static AST analysis found 59 import edges and 25 V4-C helper-symbol
  references. Runtime reflection found all 25 symbols with no failure.
- The helper, V4-C runner, and official wrapper compile/import checks passed in
  the original 4090 `safer_splat_official` environment. All four `--help`
  checks passed.
- Direct helper loading initializes CUDA and changes Python RNG state through
  dependency initialization. It did not start an experiment or write a
  repository file. The shadow adapter lazy-load boundary restores Python,
  NumPy, Torch, and already-initialized CUDA RNG states.
- A deterministic check using the real flight checkpoint and official trial 14
  compared 22 interface fields. All critical fields matched; the selected
  control was not executed and input state remained unchanged.
- R1 Stage 0 is reopened only as interface readiness. No five-context shadow
  audit, active supervisor, V4-C performance validation, or benchmark was run.
