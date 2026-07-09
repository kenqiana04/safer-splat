# SAFC Level-3B Warning-Rich Targeted Notes

## Scope

This is a targeted warning-rich discovery and activation validation. It is not
a full benchmark and does not claim performance improvement.

## Candidate Discovery

The discovery pass scanned 9
tracked reports and produced 7 unique candidates. It used
explicit H-step margin-violation or predictive-recovery evidence as
high-priority evidence. Diagnostic collision evidence was kept separate.
Referenced raw result files were not read.

Selected bounded-scan candidates: C001 (flight trial 13), C002 (flight trial 12), C003 (flight trial 14).

## No-Op Scan

Stage A computed natural repeated-control H1/H2/H3 warnings against
`dt_margin=0.0005` and executed the original `u_safe` unchanged. Candidates
passing the warning-rich gate: none.

## Active Slowdown Smoke

No naturally warning-rich candidate passed the bounded Stage-A gate. Active slowdown was not tested, and there is no activation evidence.

## Claim Boundaries

* Targeted smoke only.
* No full benchmark.
* No performance improvement claim.
* No collision reduction claim.
* No warning reduction claim.
* No planner improvement.
* No real-robot validation.
* No global safety guarantee.
* No new CBF theorem.

Claim level: `warning_rich_discovery_incomplete`.
