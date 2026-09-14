# Active Runtime V3 Paired Scientific Validation Analysis Plan

## Role and inference boundary

This is `REPEATED_BENCHMARK_PAIRED_VALIDATION_V3`. The 85 Formal V2 primary outcomes were already exposed before V3 was formed, so this is not a pristine untouched confirmatory holdout. The prespecified gates answer a bounded V2-to-V3 repair question on the frozen Stonehenge benchmark. Bootstrap intervals summarize benchmark-level paired uncertainty; they do not establish map-independent, population-level, physical-world, real-time, or deployment validity.

## Population and pairing

The primary population is exactly the Formal V2 `PRIMARY_FORMAL_85`. Each pair contains one future `ACTIVE_RUNTIME_V3` arm and the immutable, identity-verified Formal V2 `REFERENCE_CBF_QP` arm for the same trial. The 15 development-exposed trials are excluded from execution and primary analysis. All 85 pairs must be evaluation-eligible; there is no imputation or outcome-conditioned exclusion.

## Primary integrity gate

Require 85/85 eligible Active V3 arms, 85/85 eligible reused Reference arms, exact trace/lock cardinality, typed finalization, zero evidence-incomplete, zero recovery-required, zero selected/executed mismatch, zero nonfinite values, zero actuator violations, zero unresolved plant outcomes, the observed runtime radius set exactly `{0.015 q}`, and no historical-shell runtime authority.

## Primary hard-safety gate

Using posthoc no-feedback oracle evaluation at `r_hard=0.015 q` and `rho_seg=0 q`, require zero Active V3 executed swept-segment violation trials, zero Active V3 represented-map collision-proxy trials, zero Active-only hard-collision discordant pairs, and zero unresolved hard-safety oracle UNKNOWN results. The historical `0.025 q` shell is diagnostic-only and cannot change eligibility, routing, or the primary decision.

## Primary progress noninferiority gate

For every eligible pair, compute un-clipped normalized progress `(d_start-d_final)/d_start` and `delta_i=ActiveV3_i-Reference_i`. The primary estimand is the mean paired difference over all 85 pairs. Use 10,000 pair bootstrap resamples with seed `20260911` and the 95% percentile interval. PASS requires the lower confidence bound to be strictly greater than `-0.02`.

## Decision

All three primary gates must pass for `PASS_V3_PAIRED_VALIDATION_ON_FROZEN_STONEHENGE_BENCHMARK`. Integrity failure maps to `BLOCK_AND_DIAGNOSE_V3_RUNTIME_OR_EVIDENCE`; hard-safety failure maps to `FAIL_V3_HARD_SAFETY_GATE`; safety/integrity PASS with NI failure maps to `FAIL_V3_PROGRESS_NONINFERIORITY`. Fewer than 85 eligible pairs maps to `BLOCK_INCOMPLETE_PRIMARY_EVIDENCE`.

## Secondary reporting

Report paired median and distribution summaries, goal discordance, steps and termination, hard clearance at `0.015 q`, diagnostic clearance at `0.025 q`, runtime telemetry and ratios, routing roles, L1/C0/L2/L3 statuses, QP failures, deadlines, token lifecycle, typed failures, diagnostic-shell intrusion/would-reject counts, and the observed radius set. Secondary endpoints cannot replace or modify a primary gate.

## Collection separation

During future collection, only process/GPU cleanup, trace/hash integrity, source/map/runtime identity, finalization, and infrastructure state may be monitored. Aggregate progress, collision, and NI results remain uncomputed until all 85 Active V3 arms finish or a protocol-stopping integrity/safety event occurs. This freeze task executes no Active V3 arm, Reference rerun, oracle, Official100, or new Formal outcome.
