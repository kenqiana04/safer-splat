# Replica Renderer G0.5D-v2 Protocol Amendment

## Original Protocol

```text
version = G0.5D-v1
python = 3.12
habitat_sim = 0.3.3
build = official stable headless binary
decision = blocked_by_official_habitat_binary_availability
```

The v1 failure is retained as Level B: an environment-configuration
overconstraint. No renderer output, training, or SAFER run occurred under v1.

## Amended Protocol

```text
version = G0.5D-v2
python = 3.9
habitat_sim = 0.3.3
build = official stable headless binary
```

The official `aihabitat` channel provides the Linux Python 3.9
`headless_bullet` build. It is installed only in
`replica_habitat_renderer_py39`; `safer_splat_official` remains byte-identical
at its explicit Conda manifest boundary.

This is a pre-execution environment compatibility amendment, not post-result
performance tuning. The amendment neither changes the selected scene rule nor
authorizes changes to metric coordinates, frame selection, split semantics,
training, or SAFER evaluation.
