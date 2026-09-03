# Statistical Aggregation Contract V2

- The trial is the primary independent statistical unit; steps and segments are nested diagnostics, never iid replicates.
- Variants use identical trial IDs/start-goal pairs and are compared pairwise.
- Report raw, evaluable, and typed-UNKNOWN trial counts. Binary outcomes report count/rate and paired difference; continuous outcomes report trial-level distributions and paired differences.
- Runtime may have per-step descriptive summaries, but formal comparison remains trial-level and never averages only successful trials.
- Metric, subset, denominator, bootstrap/CI rule, and thresholds must be frozen before active collection. This specification invents no p-value cutoff and permits no outcome-conditioned selection.
