# FORMAL_ANALYSIS_PLAN_V2

## Primary population
`PRIMARY_FORMAL_85`: all Stonehenge trial IDs 0..99 except:
`[5,10,15,25,30,35,45,50,55,65,70,75,85,90,95]`.

The 15 excluded IDs are still run and reported descriptively.

## Primary decision gates
1. Integrity: 85/85 primary pairs evaluation-eligible; no unresolved core runtime integrity failure.
2. Safety: Active collision-proxy trials = 0; Active certification-margin violation trials = 0; Active-only collision discordances = 0.
3. Progress non-inferiority:
   - delta_i = Active progress - Reference progress
   - mean delta primary
   - 10,000 paired bootstrap resamples
   - seed 20260911
   - 95% percentile CI
   - margin = -0.02
   - PASS iff lower CI > -0.02

## Secondary analyses
- all 100 pairs descriptive;
- 15 development-exposed pairs descriptive;
- HARD/MODERATE/EASY prespecified static-geometry strata;
- median progress delta;
- goal paired discordance;
- min clearance and margin clearance;
- steps/termination;
- compute-time ratios;
- Active action roles, stage outcomes, deadlines, token events.

## Binary outcome reporting
Report n00/n01/n10/n11. Use exact McNemar only when discordant pairs exist. If an arm has zero events, report exact Clopper-Pearson 95% upper bound descriptively.

## Missing/ineligible data
No imputation. A pair enters paired analysis only if both arms are eligible. Ineligible is UNKNOWN, not safe.

## No post-hoc adaptation
No new endpoint, margin, trial exclusion, difficulty definition or parameter tuning may be introduced after aggregate formal outcomes are visible and then labeled prespecified.
