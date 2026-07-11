# V4C-HCE V0 Compact Results

This directory contains only preregistration, compact aggregate CSV/JSON, and
Markdown analysis for R-V4C-1 on flight trials 12, 13, and 14. It intentionally
excludes raw controls, per-step records, sequence records, `trials.csv`, JSONL,
trajectory samples, images, models, and checkpoints.

The formal comparator is original V4-C H3_N128. Hierarchical V0 evaluates the
original deterministic candidate space first, then invokes the untouched
original full search only if no Stage-A candidate satisfies the original
`dt_margin`. `h` is the repository GSplat safety-field value, not meter
clearance.
