# L2/H1 shadow logging completeness pilot V1

This directory contains compact, reviewable evidence for five preregistered Stonehenge `WRAPPER_ON` pilot runs. The raw per-step traces and JSONL logs remain only under the server maintenance root.

The pilot asks one bounded question: after PR #98 established control-trace non-interference, does the frozen PR #97 instrumentation leave one complete, attributable, joinable shadow observation for every independently intended committed-control/plant step?

All pilot rows are permanently marked `PILOT_QA_ONLY` and are ineligible for a formal prospective cohort. No L2 efficacy or prevalence claim is supported.

Run the task-local tests with:

```bash
python -B -m unittest discover -s reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/tests -v
```

Run the validator with:

```bash
python -B reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1/validate_l2_h1_shadow_logging_completeness_pilot_v1.py
```
