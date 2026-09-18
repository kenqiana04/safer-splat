# Post-repair V3 progress NI failure diagnosis

Frozen scientific verdict: `FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE`; integrity and represented-map hard-safety gates remain PASS. This is a post-hoc, read-only descriptive diagnosis, not a reanalysis of the gate.

## Distribution
16/85 negative trials (18.824%); bottom-five negative magnitude share 75.299%. Sample SD 0.247171, SE 0.026809; frozen CI [-0.035388, 0.069347], bootstrap mean <= -0.02 frequency 7.780%. Mean is positive but frozen lower CI does not exceed the -0.02 margin. Bottom ten: [(12, -0.834309), (97, -0.829456), (87, -0.637243), (76, -0.621266), (17, -0.322771), (71, -0.256929), (77, -0.242698), (84, -0.213952), (52, -0.083132), (33, -0.0686)].

## Routing associations
- terminal_rate_new: Pearson -0.610781823058727, Spearman -0.6763709909713662
- primary_rate_new: Pearson 0.6099431666229692, Spearman 0.6745966865336204
- retained_backup_rate_new: Pearson 0.24986477391492232, Spearman 0.5203435405484756
- L3_fail_rate_new: Pearson -0.6098232467533458, Spearman -0.6744728735178385
- fraction_last_100_cycles_terminal: Pearson -0.4872113739045843, Spearman -0.3983988436750533
- longest_terminal_run_fraction: Pearson -0.610781823058727, Spearman -0.6763709909713662
These correlations are descriptive, not causal. The trace does not expose per-attempt L3 FAIL reasons; they are `NOT_AVAILABLE`, not inferred. Bottom-ten typed pattern counts: {'EARLY_TERMINAL_LOCK_IN': 10}.

## Old to new
Old frozen verdict `FAIL_V3_HARD_SAFETY_GATE` remains unchanged. Mean paired delta 0.182829 to 0.017855; mean change -0.164974; improved/worsened/unchanged 4/81/0. Like-named routing and L3 rates are compared using each run's completed-cycle denominator; old and new trial lengths differ. Old/new change Spearman: {'terminal_rate_change': {'pearson': -0.45136799115128046, 'spearman': -0.719663037194604}, 'primary_rate_change': {'pearson': 0.4722253485552025, 'spearman': 0.7244867222814952}, 'L3_fail_rate_change': {'pearson': -0.44821055943871985, 'spearman': -0.7181607321252075}}. This does not establish that the repair caused the progress change.

## Historical witnesses
[{'trial_id': 28, 'old_hard_violation': True, 'old_min_h': -4.850638484626968e-10, 'new_hard_violation': False, 'new_min_h': 0.004600098199430576, 'old_delta': 0.0433778010729442, 'new_delta': 0.025587029736237166, 'delta_change': -0.017790771336707034, 'new_primary': 171, 'new_backup': 3, 'new_terminal': 326, 'new_L3_PASS': 171, 'new_L3_FAIL': 329, 'longest_terminal_run': 326, 'mechanism_class': 'L3_FAIL_TERMINAL_DOMINANT'}, {'trial_id': 59, 'old_hard_violation': True, 'old_min_h': -3.880511228321337e-09, 'new_hard_violation': False, 'new_min_h': 0.0024690374364931982, 'old_delta': 0.04746512357508028, 'new_delta': 0.03274680499016753, 'delta_change': -0.014718318584912751, 'new_primary': 100, 'new_backup': 12, 'new_terminal': 388, 'new_L3_PASS': 100, 'new_L3_FAIL': 400, 'longest_terminal_run': 388, 'mechanism_class': 'L3_FAIL_TERMINAL_DOMINANT'}, {'trial_id': 22, 'old_hard_violation': True, 'old_min_h': -3.3954472705710614e-09, 'new_hard_violation': False, 'new_min_h': 0.006702179509416594, 'old_delta': 0.03307776402164503, 'new_delta': 0.019755675259133743, 'delta_change': -0.013322088762511286, 'new_primary': 185, 'new_backup': 7, 'new_terminal': 308, 'new_L3_PASS': 185, 'new_L3_FAIL': 315, 'longest_terminal_run': 308, 'mechanism_class': 'L3_FAIL_TERMINAL_DOMINANT'}, {'trial_id': 57, 'old_hard_violation': True, 'old_min_h': -4.850638484626968e-10, 'new_hard_violation': False, 'new_min_h': 0.04307437714349658, 'old_delta': 0.052731246641780014, 'new_delta': -0.04511304319909211, 'delta_change': -0.09784428984087212, 'new_primary': 0, 'new_backup': 0, 'new_terminal': 500, 'new_L3_PASS': 0, 'new_L3_FAIL': 500, 'longest_terminal_run': 500, 'mechanism_class': 'EARLY_TERMINAL_LOCK_IN'}]

## Interpretation
Diagnostic classification: `D POST_REPAIR_ROUTING_SHIFT_ASSOCIATED_WITH_PROGRESS_CHANGE`. Causal-root boundary: `EVIDENCE_SUPPORTS_ROUTING_LIVENESS_MECHANISM_AS_PRIMARY_PROGRESS_FAILURE_HYPOTHESIS`. A safety-certified terminal action is not itself unsafe or erroneous. No trial was excluded, no threshold tuned, no arm rerun, and no scientific verdict changed. Next recommended task: `DESIGN_BOUNDED_POST_REPAIR_V3_LIVENESS_ROUTING_REPAIR_V1`.
