# L2/H1 Prospective Shadow Cohort Collection V1

This directory freezes the outcome-blind collection record for the 100-trial official prospective shadow cohort defined by PR #100.

The collection ran once, serially, in stable order `0..99`, with one fresh process per trial. All 100 trials passed strict logging-completeness QC. The committed evidence contains compact locks, hashes, per-trial blind QC, validation, reviews, and the outcome-blind report. Raw `.jsonl`, stdout, stderr, and scientific outcome distributions remain outside Git.

This task did not analyze L2 `PASS`/`FAIL`/`UNKNOWN`, compute a primary endpoint, alter the controller, replace a candidate, or give the shadow path control authority.

- Data role: `FORMAL_PROSPECTIVE_SHADOW_COHORT_V1`
- Validator: `PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_COLLECTION_V1_VALIDATION`
- Final status: `PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_COLLECTION_V1`
- Next task: `ANALYZE_L2_H1_PROSPECTIVE_SHADOW_COHORT_V1`
