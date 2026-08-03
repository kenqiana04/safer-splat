# ETH3D Delivery Area Protocol V2 Entry Qualification V1 — Implementation Plan

## Scope and immutable boundaries

- Metadata-only Protocol V2 entry audit.
- No ETH3D dataset archive or payload body downloads.
- No Git clone, environment creation/modification, training, optimization, map generation, controller/planner execution, route generation, or final data split generation.
- Preserve the existing reverse-proxy watchdog, managed SSH process, ports, global Git configuration, and all PRs #68–#76.
- Stage only `reproduction/cross_dataset/eth3d_delivery_area_protocol_v2_entry_qualification_v1/`.

## Frozen lineage

- Upstream PR: #76, open draft, unmerged.
- Upstream branch: `retrospective-requalify-existing-gaussian-maps-protocol-v2`.
- Upstream head: `d8fc27f7fa781ceb80e66ff12ca1a93fa0fc52de`.
- Task branch: `eth3d-delivery-area-protocol-v2-entry-qualification-v1`.
- Draft PR base: `retrospective-requalify-existing-gaussian-maps-protocol-v2`.

## Execution sequence

1. Freeze PR #76, Protocol V2, checklist, report, and run-manifest identities.
2. Fetch only official ETH3D HTML, GitHub API metadata, and small official text sources. Use HEAD only for archive URLs.
3. Resolve Delivery Area benchmark identity, high-resolution DSLR and low-resolution rig variants, exact archive metadata, and licenses.
4. Classify every official asset into immutable mapping/evaluation/reference roles and prove TRAIN/EVAL physical isolation requirements.
5. Audit the three modality routes and three frontends. Apply the preregistered selection rules without observing any trained result.
6. Freeze future split, reference, UNKNOWN, route/robot, physical-budget, evaluator, stage-gate, acquisition whitelist, denylist, and disk-budget contracts.
7. Select the fail-closed entry decision; generate machine-readable artifacts, twenty figures, and the 31-question report.
8. Run the validator from a fresh process; verify zero prohibited execution/download counts, Git staging boundaries, server report copy, disk cap, GPU cleanliness, and watchdog/SSH preservation.
9. Commit once, push the task branch, create one open Draft PR, and copy only the final `REPORT*.md` file to the desktop report directory.

## Stop conditions

Stop before any asset acquisition if official benchmark identity, archive metadata, license compatibility, legal RGB-only mapping input, official 3DGS frontend compatibility, deployable UNKNOWN path, independent reference-route path, or physical-budget derivation path cannot be established from frozen primary evidence.

## Expected success boundary

A PASS authorizes only a later bounded asset acquisition and contract audit. It does not authorize training, imply a qualified map, establish navigation safety, or grant any R/N grade.
