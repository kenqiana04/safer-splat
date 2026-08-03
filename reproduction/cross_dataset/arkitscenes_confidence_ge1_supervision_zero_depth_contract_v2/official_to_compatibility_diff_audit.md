# Official-to-Compatibility Diff Audit

- Official source: `/disk1/zlab/external_authorities/SplaTAM-da6bbcd24c248dc884ac7f49d62e91b841b26ccc/scripts/splatam.py`
- Official head: `da6bbcd24c248dc884ac7f49d62e91b841b26ccc`
- Official source SHA-256: `b8adb286bea49d6302769ec5af25af4938318044691a8996575c443e4b538816`
- Official Git blob: `1b082f7e2514da6dbecfacd9a7029c9a0389192b`
- Official checkout after tests: clean and unmodified
- Compatibility SHA-256: `8930c9d2e5172d0c56e698a418b3f454171e6c9fd84e3079d1f7c3568436a6f3`

Official mapping computes `abs(gt_depth - rendered_depth)[mask].mean()`. The frozen PR #72 microtest records a nonfinite result when that selection is empty. The compatibility function returns exactly the same masked mean when nonempty; only the empty branch returns `values.sum()*0.0`. RGB computation is supplied by and delegated to the official SplaTAM functions. Nonempty point initialization/addition is delegated to official callbacks. Empty depth skips depth initialization/addition, returns zero additions, and preserves state object identity.

No official checkout, site-package, loss weight, optimizer, learning rate, iteration count, densification/pruning rule, or NaN handling outside the empty selection was modified.
