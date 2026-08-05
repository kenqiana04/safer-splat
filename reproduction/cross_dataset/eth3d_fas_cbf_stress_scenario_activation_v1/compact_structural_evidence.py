#!/usr/bin/env python3
"""Build compact, reviewable Case-D evidence without copying large raw pools."""
from __future__ import annotations

import csv
import json
from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from task_config_v2 import METHODS, TASK_ROOT, atomic_json, sha256_file


def save_bar(name: str, title: str, labels: list[str], values: list[float]) -> None:
    figure, axis = plt.subplots(figsize=(9, 4.8))
    colors = ["#d73027" if value == 0 else "#4575b4" for value in values]
    axis.bar(labels, values, color=colors)
    axis.set_title(title)
    axis.tick_params(axis="x", rotation=30)
    axis.set_ylabel("count")
    figure.tight_layout()
    figure.savefig(TASK_ROOT / "figures" / name, dpi=170, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    candidate = json.loads(
        (TASK_ROOT / "candidate_pool/candidate_pool_summary.json").read_text(
            encoding="utf-8"
        )
    )
    v1_terminal = json.loads(
        (TASK_ROOT / "v1_semantic_audit/v1_terminal_semantics.json").read_text(
            encoding="utf-8"
        )
    )
    diagnostic = json.loads(
        (
            TASK_ROOT
            / "shadow_predicates/projected_entry_frame_diagnostic.json"
        ).read_text(encoding="utf-8")
    )
    records = diagnostic["diagnostic_records"]
    qp_feasible = [row for row in records if row["m2_qp_feasible"]]
    diagnostic_summary = {
        "status": diagnostic["status"],
        "tuple_count": diagnostic["tuple_count"],
        "plant_execution_count": diagnostic["plant_execution_count"],
        "formal_rollout_result_read_count": diagnostic[
            "formal_rollout_result_read_count"
        ],
        "endpoint_unsafe_count": diagnostic["endpoint_unsafe_count"],
        "m2_qp_feasible_count": len(qp_feasible),
        "qp_feasible_min_current_h": min(
            (row["current_h"] for row in qp_feasible if row["current_h"] is not None),
            default=None,
        ),
        "qp_feasible_min_endpoint_h": min(
            (
                row["endpoint_h"]
                for row in qp_feasible
                if row["endpoint_h"] is not None
            ),
            default=None,
        ),
        "negative_endpoint_total": sum(
            row["endpoint_h"] is not None and row["endpoint_h"] < 0
            for row in records
        ),
        "trigger_type_counts": dict(
            sorted(
                Counter(
                    row["trigger_type"] or "NOT_REACHED" for row in records
                ).items()
            )
        ),
    }
    atomic_json(
        TASK_ROOT / "shadow_predicates/projected_entry_frame_diagnostic_summary.json",
        diagnostic_summary,
    )

    pool = TASK_ROOT / "candidate_pool/candidate_pool_qualified.json"
    table = TASK_ROOT / "stage_reachability/stage_reachability_table.csv"
    identities = {
        "status": "PASS_SERVER_LARGE_ARTIFACT_IDENTITIES_RECORDED",
        "artifacts": [
            {
                "path": str(pool),
                "size_bytes": pool.stat().st_size,
                "sha256": sha256_file(pool),
                "copied_to_git": False,
                "retention": "SERVER_TASK_ROOT_ONLY",
            },
            {
                "path": str(table),
                "size_bytes": table.stat().st_size,
                "sha256": sha256_file(table),
                "copied_to_git": False,
                "retention": "SERVER_TASK_ROOT_ONLY",
            },
        ],
    }
    atomic_json(
        TASK_ROOT / "candidate_pool/server_large_artifact_identities.json", identities
    )

    counts = candidate["qualified_pool_counts"]
    requirements = {
        "G0": 28,
        "G1_NEAR": 6,
        "G1_PROJECTABLE": 16,
        "G1_UNPROJECTABLE": 6,
        "G2": 30,
        "G3_ENDPOINT_ONLY": 1,
        "G3_ENDPOINT_UNSAFE": 1,
        "G3_MARGIN": 16,
        "G4_RECOVERABLE": 18,
        "G4_UNRECOVERABLE": 8,
    }
    summary_table = TASK_ROOT / "stage_reachability/stage_reachability_summary.csv"
    with summary_table.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=("stratum", "qualified_count", "required_minimum", "gate_pass"),
            lineterminator="\n",
        )
        writer.writeheader()
        for key in requirements:
            writer.writerow(
                {
                    "stratum": key,
                    "qualified_count": counts.get(key, 0),
                    "required_minimum": requirements[key],
                    "gate_pass": counts.get(key, 0) >= requirements[key],
                }
            )

    save_bar(
        "v1_terminal_semantics.png",
        "V1 completions by method",
        list(METHODS),
        [v1_terminal["method_summary"][method]["completion_count"] for method in METHODS],
    )
    save_bar(
        "v1_activation_stage_reachability.png",
        "V1 designated-stage activation",
        ["H1", "H2", "H3", "H4"],
        [14, 0, 0, 0],
    )
    save_bar(
        "v1_h2_constraint_reduction_reconciliation.png",
        "V1 global active-constraint means",
        ["M1", "M2", "M3", "M4"],
        [
            v1_terminal["method_summary"][method][
                "active_constraints_mean_all_100_terminal_records"
            ]
            for method in METHODS[1:]
        ],
    )
    save_bar(
        "candidate_pool_funnel.png",
        "Qualified shadow strata at 200k ceiling",
        list(requirements),
        [counts.get(key, 0) for key in requirements],
    )
    save_bar(
        "stage_reachability_funnel.png",
        "G3 composition gate",
        ["endpoint unsafe", "endpoint safe / segment unsafe", "margin"],
        [
            counts.get("G3_ENDPOINT_UNSAFE", 0),
            counts.get("G3_ENDPOINT_ONLY", 0),
            counts.get("G3_MARGIN", 0),
        ],
    )
    save_bar(
        "final_decision_v2.png",
        "Case D: structural H3 activation limit",
        ["candidate tuples (x1000)", "endpoint unsafe"],
        [candidate["candidate_state_count"] / 1000, counts.get("G3_ENDPOINT_UNSAFE", 0)],
    )
    unavailable = {
        "status": "FORMAL_DEPENDENT_ARTIFACTS_NOT_GENERATED_FAIL_CLOSED",
        "reason": "The pre-lock activation gate failed at the 200000-tuple ceiling, so no registry, smoke, formal run, paired statistic, or formal-dependent figure may be generated.",
        "actual_structural_figures": sorted(
            path.name for path in (TASK_ROOT / "figures").glob("*.png")
        ),
        "formal_dependent_figures_not_generated": [
            "v2_scenario_spatial_distribution.png",
            "v2_activation_by_group.png",
            "start_safe_projectable_vs_unprojectable.png",
            "feasibility_dominance_reduction.png",
            "dt_trigger_types.png",
            "recovery_trigger_recoverability.png",
            "terminal_transition_g1.png",
            "terminal_transition_g2.png",
            "terminal_transition_g3.png",
            "terminal_transition_g4.png",
            "paired_progress.png",
            "paired_qp_infeasible.png",
            "paired_constraints.png",
            "paired_runtime.png",
            "paired_full_fas_vs_safer.png",
            "module_evidence_matrix_v2.png",
            "smoothness_diagnostics_v2.png",
            "failure_case_summary_v2.png",
        ],
    }
    atomic_json(TASK_ROOT / "report/formal_dependent_artifact_omissions.json", unavailable)
    result = {
        "status": "PASS_COMPACT_STRUCTURAL_EVIDENCE",
        "stage_summary_rows": len(requirements),
        "structural_figure_count": len(unavailable["actual_structural_figures"]),
        "server_large_artifact_count": len(identities["artifacts"]),
    }
    atomic_json(TASK_ROOT / "report/compact_structural_evidence_validation.json", result)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
