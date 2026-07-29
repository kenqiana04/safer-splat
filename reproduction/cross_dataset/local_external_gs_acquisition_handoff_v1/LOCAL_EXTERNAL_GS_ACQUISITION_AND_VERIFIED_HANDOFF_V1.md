# Local External GS Acquisition and Verified Handoff V1 Implementation Plan

> **For agentic workers:** Execute this plan inline in the existing isolated
> worktree. Do not create another branch or invoke training, rendering, map
> modification, navigation, CBF-QP, or SAFER.

**Goal:** Acquire one officially published, pretrained external Gaussian map on
the Windows host only after the user-controlled Hugging Face access gate,
freeze the primary and backup from published metadata, and create an offline,
byte-verifiable server handoff package.

**Architecture:** `local_external_gs_handoff.py` is a task-owned, staged
orchestrator. It writes all large payloads outside Git under
`%USERPROFILE%\Documents\Codex\external_gs_handoff_v1`; the worktree receives
only scripts, compact JSON evidence, the protocol, and the report. It first
checks access without logging credentials; a failed gate creates a complete
blocked handoff record and stops before any external payload operation.

**Tech stack:** Python 3.11 task-owned venv, `huggingface_hub`, `requests`,
`pandas`, standard-library ZIP64, JSON/CSV SHA-256 verification.

---

### Task 1: Freeze lineage and construct the local tool boundary

**Files:**

- Create: `reproduction/cross_dataset/local_external_gs_acquisition_handoff_v1/local_external_gs_handoff.py`
- Create: `reproduction/cross_dataset/local_external_gs_acquisition_handoff_v1/frozen_upstream_state.json`

- [ ] Read PR #60 head and compare it with `71d17db633ef5e70e394cf64b92672abe872bfd0`.
- [ ] Write immutable TUM, Splatfacto, SplaTAM, Gaussian-SLAM, Replica, budget,
  and no-execution declarations before checking Hugging Face.
- [ ] Record Python and task-owned dependency versions without changing any
  project or Conda environment.

### Task 2: Apply the user-controlled Hugging Face access gate

**Files:**

- Create: `auth_audit/MANUAL_ACTION_REQUIRED.md` outside Git when blocked
- Create: `local_hf_access_and_terms_audit.json`

- [ ] Use `HfApi.whoami` and official repository metadata calls only.
- [ ] Persist boolean access/terms evidence and redacted exception classes; never
  persist token, cookie, auth header, or command-line token argument.
- [ ] Stop at `BLOCKED_BY_LOCAL_HF_ACCESS_APPROVAL_REQUIRED` or
  `BLOCKED_BY_LOCAL_HF_NETWORK` if the gate is not passed.

### Task 3: Conditional metadata-to-candidate pipeline

**Files:**

- Create: `external_repository_revision_identity.json`
- Create: `external_scene_statistics_schema.json`
- Create: `external_candidate_precheck.json`
- Create: `external_pretrained_gs_candidate_registry.json`

- [ ] Only after access succeeds, freeze immutable revisions and download
  cards/licenses/statistics/split metadata by exact official path.
- [ ] Normalize published statistics, precheck candidates, and sort by
  `depth_l1`, descending PSNR, Gaussian count, then scene ID.
- [ ] Freeze exactly one primary and one backup before downloading a map.

### Task 4: Conditional minimal primary package

**Files:**

- Create: `primary_minimal_download_plan.json`
- Create: `materialization_audit.json`
- Create: `package_identity.json`

- [ ] Download only the frozen primary's required source files by fixed revision
  and exact paths, under the 20 GiB budget.
- [ ] Copy cache results to ordinary files, reject LFS/Xet pointers, validate
  twice from fresh processes, compute tree identities, and create a ZIP64
  package outside the handoff tree.

### Task 5: Validate and publish compact evidence

**Files:**

- Create: `validation_result.json`
- Create: `downstream_handoff.json`
- Create: `REPORT_LOCAL_EXTERNAL_GS_ACQUISITION_AND_HANDOFF_V1.md`

- [ ] Parse all compact JSON and compile all Python files.
- [ ] Stage only this task root, commit, push, and open one Draft PR based on
  `cross-dataset-qualified-gaussian-map-acquisition-v1`.

## Self-review

- No task stage may accept web terms for the user or log credentials.
- Candidate selection happens only after metadata, and payload download happens
  only after a frozen registry.
- A local acquisition pass is explicitly not a geometry, canonical-export, G0,
  or navigation qualification pass.
