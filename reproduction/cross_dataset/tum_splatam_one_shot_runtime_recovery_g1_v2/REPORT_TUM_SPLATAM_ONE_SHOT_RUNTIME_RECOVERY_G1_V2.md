# TUM SplaTAM One-Shot 4090 Runtime Recovery and Original SAFER G1 Smoke V2

## Scope and terminal decision

This task preserved the three explicitly authorized reports and synchronized the
authoritative 4090 checkout to qualified PR #44.  It then stopped at the
post-sync cleanliness gate, before any runtime import, map, query, filter,
dynamics, CBF-QP, controller, QP, or rollout action.

Terminal status: `FAIL`.

Blocking condition: `UNEXPECTED_USER_FILE_OUTSIDE_AUTHORIZED_ARCHIVE_SCOPE`.
The untracked `/disk1/zlab/projects/safer-splat/.vscode/extensions.json` is an
editor recommendation file, not a task/report asset.  The authorization only
permitted automatic relocation of the three named reports and additional files
under `work/risk_aware_cbf/`; therefore it was neither moved nor removed.
There were also 915 untracked files inside that authorized work root.  No
attempt was made to relocate that large set after the independent outside-root
block was found.

## PR and checkout identity

| Item | Value |
|---|---|
| PR #44 | `safer-world-frame-stable-ellipsoid-hessian-runtime-correction-v1` at `f63b4c496861c4f8881348d74244c1ff9a528d51` |
| Prior G1 blocker PR #45 | `fc08b03970ca16d2f3be1759b5bc840a18da918f` |
| Runtime sync PR #46 | `tum-splatam-4090-pr44-runtime-sync-v1` at `21e79b2b9a0940f957a51da6be556ef2069aae1d` |
| V2 branch base | PR #46 head above |
| pre-sync HEAD | `57c55485e357343c3d166a9123ab9a9275c12067` |
| local-only rollback branch | `maintenance/4090-pre-pr44-g1-v2-57c55485` |
| post-sync HEAD | `f63b4c496861c4f8881348d74244c1ff9a528d51` |
| `splat/distances.py` blob | `d7f17b67df40e36e458c7a5ed77c4a04659c6f35` |
| `splat/gsplat_utils.py` blob | `782c38eca50e78c605085b481155ed61e4607336` |
| `cbf/cbf_utils.py` blob | `7c6e1300b125cc0a2a950ac2835a1fbe3d0de113` |
| Numerical Contract V2 blob | `7a0d85b0b334c2e94ccc23b033d8453322d72fe1` |

The target HEAD and all four target blobs were verified after the detached
switch.  No `reset`, `clean`, force checkout, stash, core-source change, map
change, or process intervention was used.

## Authorized report preservation

Archive root:
`/disk1/zlab/maintenance_records/tum_splatam_one_shot_runtime_recovery_g1_v2/user_file_archive`

Tar archive:
`risk_aware_cbf_untracked_reports.tar`

Tar SHA-256:
`1aedcc3a8c60f63caeceeaedb235c12ead23a251266c34b06c2fd7f6e91ffe27`

| Relative source path | Source/archive SHA-256 | Byte comparison |
|---|---|---|
| `work/risk_aware_cbf/REPORT_V4C_HIERARCHICAL_CANDIDATE_EVALUATION_V0.md` | `c9ade99a1b23a877782071132a4d27da43adf1b9371a2dada4947799486485b6` | pass |
| `work/risk_aware_cbf/REPORT_VANS_SHADOW_FEASIBILITY_AUDIT.md` | `e22a150cb8f397d79c43b22ca5229ce3d043adf9d04a6b4be5ad258c5040343f` | pass |
| `work/risk_aware_cbf/paper_materials/VANS_ACTION_SEMANTICS_AUDIT.md` | `81fdfd77df1d6c4319ec1f627c6c27e61e265781bee997a0430bfb9eddda9419` | pass |

Each archive copy was made with metadata preservation, rehashed with SHA-256
and BLAKE2b, then compared byte-for-byte before its original was removed.
The server-side manifest retains the full metadata and both identities.

## Post-sync safety gate

The read-only post-switch inventory counted 916 untracked paths: 915 below
`work/risk_aware_cbf/` and one outside it:

| Path | Size | SHA-256 | Classification |
|---|---:|---|---|
| `.vscode/extensions.json` | 59 bytes | `cdfa302bad7cd93e2e1a5abae2e499ed6997b4c6a15c04ccdd451282e5276956` | user/editor configuration; outside automatic archive scope |

It is regular JSON owned by UID/GID 1000, mode `0664`, and contains an editor
extension recommendation.  It cannot be safely classified as a task/report
asset.  Leaving it untouched keeps the user file intact but prevents the
required clean-checkout gate.

## Not executed

All downstream stages are `NOT_RUN_DUE_SAFETY_GATE`: runtime imports and V2
semantic parse; asset identities; canonical map load; radius-zero regression;
robot-radius query; original filter; trial registry; initial-state diagnosis;
dynamics; CBF-QP matrix contract; one-step QP; original one-trial smoke; and
the three diagnostic trials.

Accordingly, there is no selected smoke pair, no Gaussian count/load time/GPU
memory value, no control, no collision or margin classification, no checkpoint,
and no rollout result.  Start-Safe, Risk-Aware, discrete-time verification,
predictive recovery, V4-C, 20/100-trial studies, formal training, and V1R7
were not run.

## Recommended next task

Perform a narrowly authorized server-checkout artifact reconciliation: preserve
or explicitly disposition `.vscode/extensions.json`; inventory and, if desired,
archive the 915 `work/risk_aware_cbf/` files; then re-check the detached PR #44
checkout is clean.  Only after that gate passes should this V2 protocol resume
from the environment/asset preflight.
