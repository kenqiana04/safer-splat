# Post-repair V3 paired validation: protocol and harness only

This task freezes a new prospective repaired-Active comparison against the immutable historical Formal V2 Reference, on the outcome-exposed Stonehenge benchmark. The prior V3 decision remains `FAIL_V3_HARD_SAFETY_GATE`; Pilot PASS does not retroactively change it. This branch collects no new outcome.

The 85 trial IDs, execution order, seed, 500-cycle cap, GPU mapping, 0.015 q hard radius, zero margin/rho, frozen Reference values, hard-zero integrity checks, 10,000 paired bootstrap resamples (seed 20260911), strict lower-CI > -0.02 NI rule, and witnesses 22/28/57/59 are fixed in `POST_REPAIR_V3_PAIRED_PROTOCOL.json` and the execution lock. Reference is never rerun. Historical 0.025 q is diagnostic-only and has no runtime authority.

`launch_post_repair_v3_paired_validation_v1.sh --prelaunch-check-only` is CPU-only and cannot create the future result root. An explicit later launch task is required before invoking the launcher without that flag. The launcher performs frozen preflight, creates one fresh result root, and starts a serial tmux batch; it does not run the scientific analyzer. The analyzer requires `--post-collection-authorized` and all 85 immutable repaired-Active raw evidence locks; it is a post-collection step only. Monitor reports compact trial progress without scientific peeking.

The Reference authority manifest inventories the historical immutable Formal V2 root; the separate `REFERENCE_FROZEN_OUTCOMES.json` binds exact 85 per-trial Reference hard/progress numbers to archived V3 oracle evidence. The Pilot authority manifest inventories the successful 10-trial engineering Pilot root. Large raw evidence remains at its original location. Map symlinks in the execution worktree are ignored by Git and never committed.

This is a repeatedly exposed frozen benchmark, not a pristine holdout. Any eventual new result concerns the repaired runtime on this map/cohort only; cross-scene generalization, physical safety, deployment, and real-time guarantees are not supported.
