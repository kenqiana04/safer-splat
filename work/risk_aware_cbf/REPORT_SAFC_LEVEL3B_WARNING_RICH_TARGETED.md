# REPORT: SAFC Level-3B Warning-Rich Targeted Active Slowdown

## 1. Purpose

This report searches for a naturally warning-rich targeted case and, only if
such a case is confirmed, tests whether warning-streak slowdown activates.

This is not a full benchmark. It does not claim that SAFC improves safety
performance, reduces collisions, reduces warnings, or improves planning
accuracy.

## 2. Setup

- Branch: `safc-level3b-warning-rich-targeted`
- Base commit: `47322faeb60e617dabdcbdb886f0f19574ebee22`
- Discovery sources: nine tracked reports listed in
  `candidate_source_inventory.csv`
- Selected entrypoint:
  `reproduction/scripts/run_official_runpy_smoke.py`
- Mode: `discovery-noop-then-active`
- Scene: `flight`
- `max_candidates`: 3
- `max_trials_per_candidate`: 1
- `max_steps`: 50
- `min_natural_warning_steps`: 1
- Policy scales: warning 0.75, persistent 0.50, critical 0.25
- Minimum scale: 0.25
- Official core source modified: false
- Controller modified: false
- CBF-QP modified: false
- Dynamics modified: false

The run used the existing `safer_splat_official` environment on GPU 1.
Temporary files and the Matplotlib configuration were directed to
`/disk1/zlab/tmp`.

## 3. Method

### 3.1 Candidate Discovery

The discovery script read only the nine tracked Markdown reports. It did not
read any referenced raw trace, full `trials.csv`, per-step file,
active-constraint file, trajectory sample, or JSONL file.

It produced seven unique candidates. Six had explicit H-step margin-violation
or predictive-recovery evidence and were assigned high priority. The bounded
scan selected:

- C001: flight trial 13, reported H3 recovery, count hint 28.
- C002: flight trial 12, reported H3 recovery, count hint 24.
- C003: flight trial 14, reported H3 recovery, count hint 8.

These report-derived counts were candidate-selection evidence, not evidence
that warnings would occur in the current wrapper and bounded window.

### 3.2 Targeted No-Op Scan

Stage A ran each candidate for at most 50 steps. At each step it computed the
original `u_nom` and CBF-QP `u_safe`, then performed repeated-control H=1, H=2,
and H=3 GSplat safety queries against `dt_margin=0.0005`.

The original `u_safe` was executed unchanged. No slowdown, recovery, planner,
or command-shaping action was allowed in Stage A. Only aggregate counts were
written.

### 3.3 Targeted Active Slowdown Smoke

Stage B was permitted only if a Stage-A candidate had at least one natural
warning step. No candidate passed that gate, so Stage B was not attempted.
Warnings were not injected.

## 4. Results

| Metric | Value |
| --- | ---: |
| `candidates_discovered` | 7 |
| `candidates_noop_scanned` | 3 |
| `candidates_warning_rich` | 0 |
| `active_smoke_attempted` | false |
| `active_candidate_id` | null |
| `trials_observed` | 3 |
| `steps_observed` | 150 |
| `natural_warning_steps` | 0 |
| `slowdown_active_steps` | 0 |
| `activation_observed` | false |
| `min_scale_applied` | 1.0 |
| `max_control_delta_from_slowdown` | 0.0 |
| `command_modified_only_when_warning` | true |
| `u_nom_modified` | false |
| `u_safe_internal_modified` | false |
| `wrapper_exec_command_scaled` | false |
| `collision_observed` | false |
| `qp_infeasible_observed` | false |
| `recovery_used_observed` | false |

All three candidates completed 50 no-op steps. Each had zero H1, H2, and H3
warning steps. Consequently, all three natural-warning gates failed and the
active slowdown smoke was not run.

## 5. Interpretation

No naturally warning-rich candidate was found under the bounded scan, so
active slowdown was not tested. The next step is to refine targeted case
discovery, not to claim policy effectiveness.

The tracked reports contain legitimate warning evidence in their named V4-C
contexts, but that evidence did not reproduce in the current first-50-step
official-wrapper no-op context. Possible explanations include a different
controller or trajectory context and warnings occurring outside the bounded
window. Level 3B does not resolve that difference.

The zero command delta follows from the failed natural-warning gate. It is not
evidence of safety or performance improvement.

## 6. What Level 3B Validates

- Candidate discovery from tracked compact reports was performed.
- Three report-backed candidates received a bounded no-op scan.
- The natural-warning gate prevented unsupported active execution.
- No active-policy effectiveness was validated.

## 7. What Level 3B Does Not Validate

- No full benchmark.
- No safety performance improvement.
- No collision reduction.
- No warning reduction.
- No planner integration.
- No real-robot validation.
- No global safety guarantee.
- No new CBF theorem.

## 8. Decision

Do not proceed to Level 3C. Warning-rich case discovery must be refined first,
with a fixed legitimate execution context and without presenting artificial
warning injection as natural evidence.

SAFC Level 3B validates targeted warning-rich discovery and, only if
activated, warning-gated slowdown activation in a targeted smoke.

No active slowdown activation was observed; Level 3B does not support any
active-policy effectiveness claim.
