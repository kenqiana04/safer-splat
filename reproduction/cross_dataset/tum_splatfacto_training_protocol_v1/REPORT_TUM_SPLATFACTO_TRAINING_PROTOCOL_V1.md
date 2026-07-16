# REPORT: TUM Splatfacto Training Protocol V1

## Executive Summary

This no-execution protocol depends on PR #22 at `8199c9c4c5ce76e65f389e963376a8a02d784247` and freezes one standard `splatfacto` TUM_FR1_ROOM run: seed `20260716`, 240/60 split, 30,000 iterations, and final-checkpoint-only selection.

## Evidence and Frozen Contract

Stonehenge primary reference: `/disk1/zlab/projects/safer-splat/outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml` (`cd6ea45ad01553f0ce1531ad08cfaf8359e95041b39c77291d94e75f2d2f2f8e`). Flight secondary reference: `/disk1/zlab/projects/safer-splat/outputs/flight/splatfacto/2024-09-12_172434/config.yml` (`7e83fb0711a1decc55518e66e43a34395188c2e2a2de0e5ec24d6bb510fb7b8d`). Model, optimizer, and budget match; legacy parser differences are overridden solely by the metric TUM contract.
Nerfstudio 1.1.5 uses `nerfstudio-data`; depth scale is exactly `0.0002` and standard Splatfacto depth objective is frozen false. The viewer is disabled with `--vis tensorboard`.
The NOT EXECUTED command is `exact_training_command.sh`; expected output is `/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1/splatfacto/20260716_000000`, verified absent, non-overlapping with source data, no overwrite, and no resume.

## Boundary and Handoff

No training, run directory, checkpoint, render metric, SAFER action, or G1 action occurred. Acceptance and retry gates are preregistered only. `training_iterations_executed=0`, `checkpoint_created=false`, `safer_executed=false`, and `G1_allowed=false`.
Protocol readiness is not checkpoint or SAFER readiness. The next task requires new user authorization and may execute only this frozen command; G1 baseline remains forbidden.
