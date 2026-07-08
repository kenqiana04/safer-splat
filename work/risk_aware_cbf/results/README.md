# Risk-Aware CBF Result Artifacts

This directory is reserved for lightweight release artifacts that summarize reported experiments.

Trackable result files should be small summaries, metrics, inventories, or report-adjacent markdown files, for example:

- `summary*.csv`
- `*summary*.csv`
- `metrics.json`
- `*metrics*.json`
- `*analysis*.csv`
- `*inventory*.csv`
- `*.md`

Do not commit large raw traces, per-step dumps, full trajectory samples, or trial-level raw outputs. The repository `.gitignore` keeps common raw artifacts such as `*.jsonl`, `*trace*`, `trials.csv`, `per_step*.csv`, `active_constraints.csv`, and `trajectory_samples.csv` ignored for this release branch.

