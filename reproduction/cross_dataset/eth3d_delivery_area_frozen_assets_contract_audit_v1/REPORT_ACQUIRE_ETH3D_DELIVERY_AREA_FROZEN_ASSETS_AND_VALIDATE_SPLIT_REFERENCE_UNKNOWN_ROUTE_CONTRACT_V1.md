# ETH3D Delivery Area Asset Contract Audit Stopped at the 7z Preflight Gate

## Technical summary

The PR #77 continuation passed lineage, disk, proxy-preservation, and GPU
preflight checks but could not legally start asset acquisition. The authoritative
4090 server has no existing `7z` or `7zz` executable, and the frozen protocol
explicitly forbids installing an extractor in this task. The result is therefore
the infrastructure blocker `BLOCKED_BY_7Z_RUNTIME_UNAVAILABLE`, not a dataset,
mapping, reference, UNKNOWN, route, or scientific failure.

All nine official archive downloads, all payload bytes, all environment changes,
and every training/map/controller action remain zero. PR #77, its frozen
identities, the persistent proxy watchdog, the loopback reverse tunnel, and GPU 1
were preserved.

## Frozen lineage and scope are intact

- Repository: `kenqiana04/safer-splat`
- PR #77: open, draft, unmerged, mergeable
- Base: `retrospective-requalify-existing-gaussian-maps-protocol-v2`
- Head branch: `eth3d-delivery-area-protocol-v2-entry-qualification-v1`
- Head commit: `aea42e4ec9baea5b7d4843b155b02c74a242a56b`
- Protocol V2 SHA-256: `a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e`
- New-dataset checklist SHA-256: `7c95f787fd7fb503e4bd2726546debac53acd41c1d5f9a8dd08c29cb27735593`
- PR #77 report SHA-256: `bdba615dba47e1b8a66adae82c3871682421273b0531bdc8579dffc54296198d`
- PR #77 handoff SHA-256: `8eb484d60ba73164829ac4f972be7dae517b0d3cc54097b92cd2e2ed5c7f3be5`
- Upstream payload bytes: `0`
- Upstream and current `training_authorized`: `false`

## The required archive runtime is absent

At `2026-08-04T03:14:29Z`, `/disk1` had `296,643,579,904` available bytes,
well above the 40 GB decimal minimum. The task root and data root did not exist,
so no previous task payload was mistaken for a successful acquisition.

The following read-only checks found no archive runtime:

- `type -a 7z`, `type -a 7zz`, and `type -a 7za` all failed;
- standard `/usr`, `/usr/local`, and `/bin` locations contained none;
- bounded searches of existing Conda, user-local, and `/opt` roots contained none;
- the package database reported `p7zip-full` as `not-installed`.

No installation, package modification, substitute Python extractor, or alternate
archive tool was attempted. This is exactly the frozen fail-closed condition.

## Whitelist and denylist remain frozen but untouched

The nine-item whitelist still totals `2,435,222,146` expected compressed bytes.
Its members and roles are preserved in `input_freeze/frozen_asset_manifest.json`.
The five denied archives also remain frozen. Because the 7z gate precedes the
network acquisition stage, current HEAD revalidation, downloads, SHA-256, CRC,
internal-path security checks, extraction, and tree hashes were not run.

Consequently, per-archive SHA/CRC/tree identity is **not available**, and no
asset-level PASS may be claimed. No denylist asset was requested or downloaded.

## Scientific contract stages were correctly not entered

No archive means the following evidence remains unexecuted rather than failed:

- rig image count, 237 capture groups, and four-camera grouping;
- DSLR 44-image inventory;
- camera model, pose, sparse-point provenance, and metric/depth semantics;
- rig/DSLR alignment;
- pose-only TRAIN/HELDOUT/GUARD split and its SHA;
- train-only COLMAP build and leakage audit;
- continuous reference oracle and two-engine parity;
- runtime UNKNOWN ideal-support audit;
- robot stopping-bound and route-specific map budget validation;
- reference-only PRM route registry and future evaluator freeze.

The selected modality therefore remains the PR #77 entry preference
`LOW_RES_MANY_VIEW_RIG_RGB_ONLY`; no asset-level selection or fallback decision
has been made.

## Execution and preservation evidence

| Measure | Result |
|---|---:|
| Official downloads | 0 |
| Downloaded payload bytes | 0 |
| CRC tests / extractions | 0 / 0 |
| Environment create/modify | 0 |
| Git clone / compilation | 0 / 0 |
| Training / optimizer / smoke | 0 / 0 / 0 |
| Model or Gaussian map | 0 |
| Controller / planner benchmark | 0 / 0 |
| Reference-only route generation | 0 |
| Candidate-map access | 0 |
| ICP/Sim(3) / scale repair | 0 / 0 |
| Frame deletion | 0 |

GPU 1 ended at 6 MiB, 0% utilization, and zero compute processes. The scheduled
task `Codex-Persistent-Reverse-Proxy-Watchdog` remained `Running`; the managed
reverse SSH process was PID 4904; the remote listener remained loopback-only at
`127.0.0.1:17898`. No watchdog, SSH, port 17897, sshd, network, firewall, or
global Git proxy setting was changed.

## Limitations and exact resume point

This report certifies only a pre-download infrastructure blocker. It does not
qualify any ETH3D asset, split, reference geometry, runtime UNKNOWN rule, route,
physical budget, evaluator, input adapter, environment, learned map, or safety
claim.

The exact resume point is `PRE_DOWNLOAD_7Z_RUNTIME_GATE`. A separate explicit
authorization must make an existing `7z` or `7zz` runtime available. The same
branch, PR #77 lineage, whitelist, denylist, content lengths, and frozen
scientific contracts must then be reused; no result exists to redownload or
replace.

## Decision

`FINAL_STATUS=BLOCKED_BY_7Z_RUNTIME_UNAVAILABLE`

`FINAL_DECISION=STOP_BEFORE_DOWNLOAD_AND_REQUEST_SEPARATE_7Z_RUNTIME_PROVISIONING_AUTHORIZATION`

`training_authorized=false`

`Only next task=SEPARATELY_AUTHORIZE_EXISTING_7Z_RUNTIME_PROVISIONING_AND_RESUME_THIS_SAME_TASK`
