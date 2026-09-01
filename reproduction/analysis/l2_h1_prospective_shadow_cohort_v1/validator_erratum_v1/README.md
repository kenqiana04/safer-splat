# Case-C-aware Validator Erratum V1

This directory contains an independent, minimal validator erratum for the already-revealed Case C result. It does not replace or edit `../validate_formal_analysis_v1.py` and does not overwrite `../validation_result.json`.

The original validator history remains authoritative evidence: 21 checks passed and only `bootstrap_contract_exact` failed because that implementation unconditionally required 10,000 valid replicates. The frozen protocol also contains a second legal terminal path: after 100,000 total draws, fewer than 10,000 valid replicates must yield `BOOTSTRAP_NOT_ESTIMABLE` with no point estimate or CI.

`validate_case_c_erratum.py` verifies only that original failure boundary, the frozen bootstrap terminal contract, the exact Case C compact values, and every post-reveal scientific artifact hash. It never reads raw rows, rebuilds the canonical table, reruns bootstrap, or implements the other 21 checks.

Run:

```text
python -B validate_case_c_erratum.py --task-dir .. --output erratum_validation_result.json
```
