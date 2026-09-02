# Deadline and Backup Token Compatibility Audit V2

Verdict: `COMPATIBLE_WITHOUT_LOGIC_CHANGE`.

PR #107 retains a valid old backup while new evidence is pending and activates replacement only at successful navigation commit. PR #110 distinguishes discovery from consumption:

- New L3 backup discovery/computation is high-cost work and may begin only when the deadline contract permits it. It cannot begin at WARNING or EXPIRED.
- Activation of a COMPLETE prepared bundle tied to an already-certified selected navigation commit is an atomic handoff, not new discovery.
- Consumption of an already ACTIVE and VALID retained token remains a legal expired-deadline choice after exact validity and action-identity checks.

No PR #107 state-machine or PR #110 deadline rule is modified. Deadline expiry never validates an invalid token, constructs a token, or authorizes a terminal action.
