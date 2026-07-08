# Risk-Aware CBF Reproducibility Manifest

The canonical paper-release audit is the repository-level
`REPRODUCIBILITY_MANIFEST.md`.

This scoped manifest records the local policy for `work/risk_aware_cbf/`:

- report markdown files are intended to remain tracked;
- lightweight scripts belong in `work/risk_aware_cbf/scripts/`;
- compact summaries, metrics, inventories, and report-adjacent markdown belong in `work/risk_aware_cbf/results/` or `work/risk_aware_cbf/metrics/`;
- raw traces, per-step dumps, trial-level raw CSVs, and trajectory samples should not be committed.

The audited GitHub snapshot contains the reports, many notes, figures, and paper-material files, but it does not contain the concrete Python scripts or compact summary/metrics files referenced by several reports. See the repository-level manifest for the per-report matrix.
