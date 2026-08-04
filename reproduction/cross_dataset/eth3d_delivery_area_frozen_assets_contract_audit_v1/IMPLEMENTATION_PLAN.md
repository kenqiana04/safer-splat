# ETH3D Delivery Area Frozen Assets Contract Audit V1 Implementation Plan

> **For agentic workers:** Execute this plan inline and fail closed at every
> frozen gate. Steps use checkbox (`- [x]` or `- [ ]`) syntax for tracking.

**Goal:** Acquire exactly nine frozen official ETH3D Delivery Area archives and
freeze the split/reference/UNKNOWN/route contracts without creating an
environment, training, or map.

**Architecture:** PR #77 identities and the asset whitelist are frozen before
remote access. A mandatory disk and archive-runtime preflight precedes every
network request. Asset, geometry, split, route, and evaluator stages run only
after archive identity, CRC, security, and physical-isolation gates pass.

**Tech Stack:** Git, SSH, curl through the existing proxy wrapper, 7z/7zz,
Python standard library, COLMAP text parsing, deterministic JSON/CSV evidence.

---

### Task 1: Freeze lineage and boundaries

**Files:**
- Create: `input_freeze/pr77_lineage.json`
- Create: `input_freeze/frozen_asset_manifest.json`

- [x] Confirm PR #77 is open, draft, unmerged, mergeable, and at the frozen head.
- [x] Confirm Protocol V2, checklist, report, and downstream handoff identities.
- [x] Freeze the nine-item whitelist and five-item denylist.

### Task 2: Run pre-download gates

**Files:**
- Create: `preflight/runtime_preflight.json`

- [x] Verify at least 40 GB decimal free under `/disk1/zlab`.
- [x] Verify the persistent proxy wrapper and loopback listener are preserved.
- [x] Search PATH, standard locations, existing Conda roots, user-local roots,
  and `/opt` for `7z` or `7zz` without installing software.
- [x] Stop with `BLOCKED_BY_7Z_RUNTIME_UNAVAILABLE` because the required
  executable is absent.

### Task 3: Acquire and validate the frozen archives

**Files:**
- Planned: archive identities, CRC/security manifests, and extracted-tree hashes.

- [ ] Revalidate frozen official URL metadata.
- [ ] Download exactly nine archives atomically and sequentially.
- [ ] Run CRC, internal-path security, and quarantine extraction checks.

This task is intentionally not started because Task 2 failed.

### Task 4: Freeze scientific contracts

**Files:**
- Planned: rig/DSLR inventories, split manifests, train-only COLMAP identity,
  reference/UNKNOWN/budget/route/evaluator contracts.

- [ ] Audit rig and DSLR assets.
- [ ] Generate the pose-only split and train-only COLMAP model.
- [ ] Validate metric/reference/UNKNOWN/budget/route contracts.

This task is intentionally not started because no archive was downloaded.

### Task 5: Record and publish the blocker

**Files:**
- Create: `run_manifest.json`
- Create: `validation_result.json`
- Create: `downstream_handoff.json`
- Create: `REPORT_ACQUIRE_ETH3D_DELIVERY_AREA_FROZEN_ASSETS_AND_VALIDATE_SPLIT_REFERENCE_UNKNOWN_ROUTE_CONTRACT_V1.md`

- [x] Record zero execution counts and the exact failed preflight evidence.
- [x] Preserve PR #77, watchdog, reverse tunnel, GPU state, and all prohibited
  execution boundaries.
- [ ] Validate JSON/report consistency, commit, push, and open one Draft PR.
