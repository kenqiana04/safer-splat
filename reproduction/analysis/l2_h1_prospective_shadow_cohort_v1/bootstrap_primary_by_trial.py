#!/usr/bin/env python3
"""Frozen trial-cluster bootstrap for the primary signal rate."""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Any

from analysis_common import atomic_write_json, load_json, percentile


def bootstrap_by_trial(per_trial: list[dict[str, Any]], *, valid_replicates: int = 10000, maximum_total_draws: int = 100000,
                       seed: int = 20260831) -> dict[str, Any]:
    rng = random.Random(seed)
    cluster_count = len(per_trial)
    rates: list[float] = []
    total_draws = zero_draws = 0
    while len(rates) < valid_replicates and total_draws < maximum_total_draws:
        total_draws += 1
        sampled = [per_trial[rng.randrange(cluster_count)] for _ in range(cluster_count)] if cluster_count else []
        denominator = sum(int(row["N_primary"]) for row in sampled)
        if denominator == 0:
            zero_draws += 1
            continue
        rates.append(sum(int(row["N_FAIL"]) for row in sampled) / denominator)
    estimable = len(rates) == valid_replicates
    pooled_denominator = sum(int(row["N_primary"]) for row in per_trial)
    pooled_numerator = sum(int(row["N_FAIL"]) for row in per_trial)
    return {
        "schema_version": "L2_H1_FORMAL_PRIMARY_TRIAL_CLUSTER_BOOTSTRAP_V1",
        "status": "ESTIMABLE" if estimable else "BOOTSTRAP_NOT_ESTIMABLE", "cluster_unit": "formal_trial",
        "cluster_count": cluster_count, "clusters_per_replicate": cluster_count, "resampling": "WITH_REPLACEMENT",
        "rng_seed": seed, "ci_method": "95_PERCENT_PERCENTILE_LINEAR", "step_iid_assumption": False,
        "p_value_or_significance_test": False, "bootstrap_valid_replicates": len(rates), "bootstrap_total_draws": total_draws,
        "bootstrap_zero_denominator_draws": zero_draws,
        "bootstrap_point_estimate_check": pooled_numerator / pooled_denominator if pooled_denominator else None,
        "bootstrap_ci_low": percentile(rates, 0.025) if estimable else None,
        "bootstrap_ci_high": percentile(rates, 0.975) if estimable else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-trial-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = load_json(args.per_trial_json)
    atomic_write_json(args.output, bootstrap_by_trial(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

