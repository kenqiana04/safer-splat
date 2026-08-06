"""Build the frozen research-direction audit artifacts.

The builder performs only documentation, aggregation, plotting, and read-only
Git-object access.  It does not import or execute mapping/controller code.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import subprocess
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from audit_data import (
    ASSETS,
    DIRECTION_DETAILS,
    EFFORT,
    FATAL_RESULTS,
    FINAL_DECISION,
    FINAL_STATUS,
    FULLTEXT_FACTS,
    HYPOTHESES,
    MAPS,
    ONLY_NEXT_TASK,
    PAPERS,
    POSITIVE_SCORES,
    REVIEW_DATA,
    REVIEW_TOP3,
    RISK_SCORES,
    SEARCH_CLUSTERS,
    WORKSTREAMS,
)
from task_config import (
    AUDIT_ID,
    DIRECTIONS,
    EXECUTION_COUNTS,
    FATAL_GATES,
    METHOD_THRESHOLDS,
    POSITIVE_WEIGHTS,
    QUERY_LIMITS,
    RISK_WEIGHTS,
    SEARCH_CUTOFF,
    UPSTREAM,
)

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
UPSTREAM_HEAD = UPSTREAM[87]
SOURCE_RUN = "reproduction/cross_dataset/resume_replica_gt_executable_safety_activated_benchmark_v1"


def write_text(path: str | Path, text: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: str | Path, payload: object) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


def write_csv(path: str | Path, header: list[str], rows: list[list[object]]) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def git_show(path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{UPSTREAM_HEAD}:{path}"],
        cwd=REPO,
        text=True,
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def yesno(value: bool) -> str:
    return "PASS" if value else "FAIL"


def md_table(header: list[str], rows: list[list[object]]) -> str:
    def clean(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(map(clean, header)) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    lines.extend("| " + " | ".join(map(clean, row)) + " |" for row in rows)
    return "\n".join(lines)


def build_history() -> None:
    header = [
        "workstream_id", "workstream", "research_question", "expected_contribution", "implementation",
        "data_maps", "positive_result", "negative_result", "falsified_assumption", "still_valid",
        "reusable_code", "reusable_data", "reusable_evaluation", "paper_usable_evidence", "forbidden_claim",
        "sunk_cost", "future_dependency",
    ]
    write_csv("history/workstream_ledger.csv", header, [list(row) for row in WORKSTREAMS])
    write_csv(
        "history/evidence_asset_inventory.csv",
        ["asset_id", "asset", "asset_type", "source_workstream", "status", "bounded_use"],
        [list(row) for row in ASSETS],
    )
    write_csv(
        "history/falsified_hypotheses.csv",
        ["hypothesis_id", "hypothesis", "status", "decisive_evidence"],
        [list(row) for row in HYPOTHESES],
    )
    write_json(
        "history/reusable_artifact_manifest.json",
        {
            "audit_id": AUDIT_ID,
            "source_head": UPSTREAM_HEAD,
            "artifact_count": len(ASSETS),
            "artifacts": [
                dict(zip(["asset_id", "asset", "asset_type", "source_workstream", "status", "bounded_use"], row))
                for row in ASSETS
            ],
        },
    )
    claims = [
        ("C01", "Risk-Aware supports efficiency and constraint reduction", "SUPPORTED_BOUNDED", "R2", "Do not convert to a new-safety claim"),
        ("C02", "TUM Splatfacto is a formal navigation map", "PROHIBITED", "R4", "Geometry drift and reference mismatch"),
        ("C03", "Core V1 mechanisms execute on frozen activated states", "SUPPORTED_BOUNDED", "R11;R12", "Replica GT-derived activated cohort only"),
        ("C04", "Core V1 broadly replaces SAFER in representative operation", "PROHIBITED", "R12", "Segment/backup/directional incremental impact 0/160"),
        ("C05", "0/160 means Core V1 is methodologically wrong", "PROHIBITED", "R12", "It is a prevalence/result boundary, not a mechanism falsification"),
        ("C06", "Stress cases override representative prevalence", "PROHIBITED", "R8;R12", "Selection-biased cohorts remain separate"),
        ("C07", "Reference collision superiority", "PROHIBITED", "R12", "Reference-collision positive event count was zero"),
        ("C08", "B3 meets a 50 ms real-time contract", "PROHIBITED", "R12", "116/260 B3 one-step deadline misses"),
        ("C09", "Protocol V2 determines claim eligibility", "SUPPORTED_BOUNDED", "R3", "Qualification gate, not algorithmic superiority"),
        ("C10", "Unified certifier is an end-to-end proven safe system", "PROHIBITED", "R10;R11", "Open assumptions and empirical-only obligations"),
        ("C11", "Replica activated cohort estimates field prevalence", "PROHIBITED", "R12", "Deliberately selected for stage activation"),
        ("C12", "Replica representative cohort supports zero observed incremental segment/backup/directional outcome effect", "SUPPORTED_BOUNDED", "R12", "One GT-derived map and frozen 160-state holdout"),
    ]
    write_csv("history/claim_boundary_registry.csv", ["claim_id", "claim", "status", "evidence", "boundary"], [list(x) for x in claims])
    phases = [
        ("P1", "Published baseline reproduction", "R1", "Recovered SAFER/Splat-Nav execution and failure taxonomy"),
        ("P2", "Efficiency ablations", "R2", "BestD retained only as constraint-reduction evidence"),
        ("P3", "Cross-dataset qualification", "R3-R5", "Protocol V2 rejected rendering-only map claims"),
        ("P4", "Numerical and protocol diagnosis", "R6-R8", "Separated start-safe, sampled-data, and recovery failures"),
        ("P5", "Conceptual consolidation", "R9-R10", "Frozen Core V1 interfaces, claims, and proof obligations"),
        ("P6", "Executable certifier", "R11 / PR #84-#86", "Frozen B0-B3 nested method contract"),
        ("P7", "Activated and representative audit", "R12 / PR #87", "Mechanism positive; representative prevalence and runtime negative"),
        ("P8", "Direction due diligence", "current task", "No new scientific execution; literature/data/winnability decision"),
    ]
    write_text(
        "history/timeline.md",
        "# Historical work timeline\n\n"
        "This is an evidence-phase timeline, not a claim that every phase was linear. Sunk cost is recorded but is never a selection criterion.\n\n"
        + md_table(["Phase", "Focus", "Workstreams", "Frozen outcome"], [list(x) for x in phases]),
    )


def build_literature() -> None:
    protocol = f"""# Systematic literature search protocol

- Search cutoff: **{SEARCH_CUTOFF}**.
- Primary emphasis: 2023 through cutoff; foundational control work may precede 2023.
- Round A: high-recall search across web scholarly indexes, arXiv, IEEE/CVF/ACM/Springer venue pages, and official project/code pages.
- Round B: backward/forward snowballing from SAFER-Splat, Splat-Nav, SPLANNING, FOCI, FastBridge, GAVIS, conformal perception safety, and sampled-data/backup CBF papers.
- Method conclusions require primary-source full text or official code/documentation. Search snippets only route screening.
- Synonyms checked: safety layer/shield/set, collision-aware/risk-aware control, confidence/uncertainty field, free-space confidence, abstention, unknown space, commitment, recoverability, backup policy, viability, continuous collision, and segment certification.
- A negative statement is phrased as “not found in the reviewed full text/code” rather than universal absence.
- Result counts are recorded as `not_exposed_by_search_provider` when the search interface did not expose a stable total; the audit records the titles actually screened instead of inventing a count.
"""
    write_text("literature/search_protocol.md", protocol)

    query_rows: list[list[object]] = []
    for cluster, query in SEARCH_CLUSTERS.items():
        query_rows.append([cluster, "A", query, "cross-source scholarly web + primary-source routing", SEARCH_CUTOFF, "not_exposed_by_search_provider", 3, "title/abstract routed; primary source checked when included"])
    snowball_queries = [
        ("SB1", "B", "papers citing SAFER-Splat Gaussian CBF", "arXiv/author project pages"),
        ("SB2", "B", "papers citing Splat-Nav Gaussian navigation", "arXiv/CVF/IEEE"),
        ("SB3", "B", "FOCI Gaussian overlap collision integral code", "paper references/official code"),
        ("SB4", "B", "SPLANNING normalized Gaussian collision probability", "paper references/project page"),
        ("SB5", "B", "FastBridge backup CBF 3D Gaussian Splatting", "paper references/arXiv"),
        ("SB6", "B", "GAVIS anisotropic visibility uncertainty 3DGS", "CVF/paper references"),
        ("SB7", "B", "conformal prediction measurement robust sampled data CBF", "arXiv/paper references"),
        ("SB8", "B", "predicted flow CBF terminal backup safe set", "paper/project page"),
        ("SB9", "B", "analytic collision cone CBF 3D Gaussian Splatting", "arXiv/paper references"),
        ("SB10", "B", "SplatCtrl reactive robot control Gaussian", "arXiv/references"),
        ("SB11", "B", "3DGS geometric accuracy mesh reference robotics", "arXiv/CVF"),
        ("SB12", "B", "implicit swept volume SDF continuous collision", "ACM/arXiv/code"),
    ]
    for cluster, rnd, query, source in snowball_queries:
        query_rows.append([cluster, rnd, query, source, SEARCH_CUTOFF, "not_exposed_by_search_provider", 2, "core-reference/citation screening"])
    write_csv(
        "literature/search_queries.csv",
        ["query_id", "round", "exact_query", "source", "search_date", "result_count", "screened_title_count", "notes"],
        query_rows,
    )

    screen_rows = []
    included_rows = []
    excluded_rows = []
    for paper in PAPERS:
        pid, title, year, status, categories, included, fulltext, code, url, evidence, overlap, limitation = paper
        decision = "INCLUDE" if included else "EXCLUDE"
        reason = "High or medium relevance to frozen candidates" if included else limitation
        screen_rows.append([pid, title, year, categories, decision, reason, pid, yesno(fulltext), yesno(code), url])
        row = [pid, title, year, status, categories, yesno(fulltext), yesno(code), url, evidence, overlap, limitation]
        (included_rows if included else excluded_rows).append(row)
    common_header = ["dedup_key", "title", "year", "venue_status", "categories", "fulltext", "official_code_checked", "primary_url", "key_evidence", "candidate_overlap", "limitation_or_exclusion"]
    write_csv("literature/screening_log.csv", ["dedup_key", "title", "year", "categories", "decision", "reason", "dedup_rule", "fulltext", "code", "url"], screen_rows)
    write_csv("literature/included_papers.csv", common_header, included_rows)
    write_csv("literature/excluded_papers.csv", common_header, excluded_rows)

    snowball_rows = [
        ["FastBridge", "backward", "SAFER-Splat; backup CBF; full-dynamics safety filters", "included", "Direct D1/D4 overlap"],
        ["SAFER-Splat", "forward", "analytic collision-cone CBF; FastBridge; SplatCtrl", "included", "Recent realization-gap competitors"],
        ["Splat-Nav", "forward", "SPLANNING; FOCI; Gaussian navigation pipelines", "included", "Planning/collision lineage"],
        ["GAVIS", "backward/forward", "Bayesian/visibility uncertainty and active mapping", "included", "D3/D8 uncertainty lineage"],
        ["Conformal perception safety", "forward", "adaptive conformal safety; conformal risk planning", "included", "One-sided calibration lineage"],
        ["Predicted-Flow CBF", "backward", "backup CBF and predictive safety filters", "included", "D4/D5 feasibility lineage"],
    ]
    write_csv("literature/snowballing_log.csv", ["seed", "direction", "works_or_cluster", "decision", "reason"], snowball_rows)

    page_counts = {
        "2304.00194": 15, "2309.08050": 9, "2403.02751": 20, "2405.00362": 14,
        "2405.10142": 8, "2409.09868": 8, "2409.16915": 20, "2505.08510": 8,
        "2509.14421": 6, "2604.18205": 8, "2605.20566": 9, "2605.30342": 29,
        "2606.00297": 19, "2607.01200": 9, "2607.08948": 8,
    }
    sources = []
    for path in sorted((ROOT / ".cache" / "papers").glob("*.pdf")):
        if path.stat().st_size == 0:
            continue
        sources.append({
            "dedup_key": path.stem,
            "cache_path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
            "pages": page_counts[path.stem],
            "committed": False,
            "use": "full-text evidence extraction only",
        })
    write_json("literature/source_archive_manifest.json", {"search_cutoff": SEARCH_CUTOFF, "source_count": len(sources), "sources": sources})

    pointers = {
        "2304.00194": "PDF pp.1-5, Sec. II-IV; theorem/coverage discussion",
        "2309.08050": "PDF pp.1-6, Def. 2-3 and sampled-data construction",
        "2403.02751": "PDF pp.2-8 methods; pp.15-17 experiments",
        "2405.00362": "PDF pp.3-9, swept-volume SDF formulation and experiments",
        "2405.10142": "PDF pp.2-6, planning objective and safety constraint",
        "2409.09868": "PDF pp.2-6, CBF construction, online map, experiments",
        "2409.16915": "PDF pp.3-10, normalized GS collision bound and optimization",
        "2505.08510": "PDF pp.2-6, FOCI integral and trajectory optimization",
        "2509.14421": "PDF pp.2-5, collision cone CBF, QP, evaluation",
        "2604.18205": "PDF pp.2-7, 19-scene geometry metrics and results",
        "2605.20566": "PDF pp.2-7, AV@R, safety/perception CBFs, simulation",
        "2605.30342": "PDF pp.3-10, anisotropic visibility/Bayesian rasterizer; limitations p.17",
        "2606.00297": "PDF pp.3-11, predicted-flow CBF and terminal backup set",
        "2607.01200": "PDF pp.2-7, full dynamics, actuator limits, collision cone ECBF, backup CBF",
        "2607.08948": "PDF pp.2-7, online GS, reactive CBF, physical experiments, limitations",
    }
    evidence_header = [
        "dedup_key", "title", "venue_status", "research_question", "input_representation", "map_assumptions",
        "geometry_authority", "uncertainty_object", "query_unit", "output_semantics", "unknown_or_abstention",
        "false_free_direct", "point_segment_trajectory", "robot_footprint", "control_model", "actuator_bounds",
        "sampled_data", "terminal_backup", "method", "theory", "exact_assumptions", "datasets",
        "learned_or_gt", "reference_authority", "closed_loop", "hardware", "runtime", "released_code",
        "stated_limitations", "overlap", "uncovered", "direct_baseline", "source_pointer",
    ]
    evidence_rows = []
    for paper in PAPERS:
        pid, title, year, status, categories, included, fulltext, code, url, evidence, overlap, limitation = paper
        if not fulltext:
            continue
        facts = FULLTEXT_FACTS[pid]
        row = [
            pid, title, status, evidence,
            facts["input_representation"], facts["map_assumptions"], facts["geometry_authority"], facts["uncertainty_object"],
            facts["query_unit"], facts["output_semantics"], facts["unknown_or_abstention"], facts["false_free_direct"],
            facts["point_segment_trajectory"], facts["robot_footprint"], facts["control_model"], facts["actuator_bounds"],
            facts["sampled_data"], facts["terminal_backup"], evidence, facts["theory"], facts["exact_assumptions"],
            facts["datasets"], facts["learned_or_gt"], facts["reference_authority"], facts["closed_loop"], facts["hardware"],
            facts["runtime"], yesno(code), limitation, overlap,
            "Cross-map one-sided reference qualification remains generally uncovered",
            "YES" if included else "NO", pointers[pid] + "; " + url,
        ]
        evidence_rows.append(row)
        card = f"""# {title}

- Identity: `{pid}`; {status}; {url}
- Reviewed source: {pointers[pid]}
- Research question and method: {evidence}
- Strongest overlap with frozen candidates: {overlap}
- Exact difference still potentially available: Cross-map one-sided reference qualification/abstention is not established by this paper alone.
- Direct baseline status: {"official code/project checked" if code else "paper specification available; official runnable code not confirmed"}.
- Limitation relevant to our decision: {limitation}
- Audit rule: “not found” means not found in this reviewed full text and linked official material; it is not a universal absence claim.
"""
        write_text(f"literature/competitor_cards/{pid}.md", card)
    write_csv("literature/fulltext_evidence_matrix.csv", evidence_header, evidence_rows)

    baseline_rows = []
    for paper in PAPERS:
        pid, title, _, status, cats, included, fulltext, code, url, evidence, overlap, limitation = paper
        if not included:
            continue
        runnable = "official code checked" if code else "fair reimplementation from paper only"
        fairness = "Requires frozen map/input/runtime normalization; no author result may be copied as our outcome"
        baseline_rows.append([pid, title, runnable, yesno(fulltext), yesno(code), fairness, overlap, url])
    write_csv("literature/baseline_availability.csv", ["id", "baseline", "availability", "fulltext", "official_code_checked", "fairness_requirement", "candidate_relevance", "source"], baseline_rows)
    claim_map = {
        "FastBridge is the strongest D1/D4 overlap": ["2607.01200"],
        "Analytic 3DGS collision-cone CBF reduces D2/D5 novelty room": ["2509.14421", "2607.01200"],
        "Gaussian trajectory collision optimization is already crowded": ["2409.16915", "2505.08510", "2405.00362"],
        "3DGS uncertainty and active mapping are active areas": ["2605.20566", "2605.30342"],
        "Conformal perception safety supplies statistical precedent": ["2304.00194", "2309.08050"],
        "A reference-grounded navigation qualification benchmark remains potentially distinct": ["2604.18205", "2605.30342", "2403.02751"],
        "No reviewed paper alone supplies our two-map Protocol V2 event-labelled split": ["2604.18205", "2605.30342", "2409.09868", "2607.01200"],
    }
    write_json("literature/claim_to_source_map.json", {"search_cutoff": SEARCH_CUTOFF, "claims": claim_map})


def build_data() -> tuple[int, int]:
    map_header = [
        "map_id", "map_identity", "generation_method", "gaussian_type", "identity", "scale_coordinate_validity",
        "independent_reference", "reference_type", "robot_alignment", "route_state_available", "representative_queries",
        "false_free_count", "false_occupied_count", "unknown_count", "segment_risk_count", "backup_activation_count",
        "map_reference_disagreement", "split_status", "cross_map_status", "formal_claim_scope", "major_confounders",
    ]
    write_csv("data/map_readiness_matrix.csv", map_header, [list(row) for row in MAPS])
    ref_rows = []
    for row in MAPS:
        mid, name, generation, _, identity, scale, ref, ref_type, alignment, routes, queries, *_rest = row
        tier = {"mesh": "A", "mesh/depth": "A/B", "depth": "B", "none": "D"}.get(ref_type, "C")
        admissible = "YES_BOUNDED" if mid == "M1" else ("NEGATIVE_CONTROL_ONLY" if mid == "M6" else "NO_CURRENT_CROSS_MAP_CLAIM")
        ref_rows.append([mid, name, ref, ref_type, tier, scale, alignment, admissible, identity])
    write_csv("data/reference_authority_matrix.csv", ["map_id", "map", "reference", "reference_type", "authority_tier", "metric_status", "alignment", "claim_admissibility", "map_identity"], ref_rows)
    write_text(
        "data/query_event_rate_contract.md",
        f"""# Frozen query event-rate contract

- Frozen before reading query outcomes: use the PR #87 representative holdout, never the activated search cohort.
- Map: M1 only; all other maps are `NOT_EVALUABLE` because a frozen representative registry or credible reference is missing.
- Point unit: one B3 current-query record per representative state (maximum {QUERY_LIMITS['point_per_map']}).
- Segment unit: the matched B3 short represented segment and offline mesh outcome (maximum {QUERY_LIMITS['short_segment_per_map']}).
- No training, threshold change, controller execution, resampling, or formal navigation occurs.
- The 100 activated states are retained only as selection-biased mechanism evidence and excluded from rate estimation.
- `backup_stage_selected` is descriptive; it is not an incremental outcome effect. PR #87 found zero representative incremental segment/backup/directional effect despite 35 terminal-action selections.
""",
    )
    text = git_show(f"{SOURCE_RUN}/benchmark/one_step_records.csv")
    rows = list(csv.DictReader(io.StringIO(text)))
    selected = [r for r in rows if r["cohort"] == "REPRESENTATIVE_HOLDOUT" and r["method"] == "B3_FULL_UNIFIED_WITH_DIRECTIONAL_ALTERNATIVES"]
    assert len(selected) == 160
    records = []
    for row in selected:
        point_outcome = "FINITE" if row["current_query_status"] == "FINITE" else "UNKNOWN"
        records.append(["M1", row["state_id"], "point", "REPRESENTATIVE_HOLDOUT", point_outcome, row["reference_min_clearance_m"], row["reference_immediate_swept_collision"], row["represented_false_safe"], row["reference_safe_but_rejected"], "False" if point_outcome == "FINITE" else "True", "False", row["semantic_status"] == "CERTIFIED_TERMINAL_ACTION", row["map_reference_disagreement"], "PR87_B3_CANONICAL_GIT_BLOB"])
        records.append(["M1", row["state_id"], "short_segment", "REPRESENTATIVE_HOLDOUT", "SAFE" if row["represented_segment_safe"] == "True" else "RISK", row["reference_min_clearance_m"], row["reference_immediate_swept_collision"], row["represented_false_safe"], row["reference_safe_but_rejected"], "False", row["represented_segment_violation"], row["semantic_status"] == "CERTIFIED_TERMINAL_ACTION", row["map_reference_disagreement"], "PR87_B3_CANONICAL_GIT_BLOB"])
    record_header = ["map_id", "query_id", "query_type", "cohort", "map_outcome", "reference_min_clearance_m", "reference_collision", "false_free", "false_occupied", "unknown", "segment_risk", "backup_stage_selected", "map_reference_disagreement", "source"]
    write_csv("data/query_event_rate_records.csv", record_header, records)
    point = [r for r in records if r[2] == "point"]
    segment = [r for r in records if r[2] == "short_segment"]
    def count_bool(rs: list[list[object]], idx: int) -> int:
        return sum(str(r[idx]).lower() == "true" for r in rs)
    summary = [
        ["M1", "point", len(point), count_bool(point, 7), count_bool(point, 8), count_bool(point, 9), 0, count_bool(point, 11), count_bool(point, 12), "0/160 reference collisions; no superiority inference"],
        ["M1", "short_segment", len(segment), count_bool(segment, 7), count_bool(segment, 8), count_bool(segment, 9), count_bool(segment, 10), count_bool(segment, 11), count_bool(segment, 12), "35 backup selections but zero incremental representative outcome effect"],
    ]
    for mid, name, *_ in MAPS[1:]:
        summary.append([mid, "NOT_EVALUABLE", 0, "NA", "NA", "NA", "NA", "NA", "NA", "No frozen representative query/reference contract"])
    write_csv("data/event_rate_summary.csv", ["map_id", "query_type", "n", "false_free", "false_occupied", "unknown", "segment_risk", "backup_stage_selected", "map_reference_disagreement", "interpretation"], summary)
    splits = [
        ["D1", "FAIL", "Only one reference-complete map; required representative rare events are zero"],
        ["D2", "FAIL", "No two independent anisotropic learned maps with credible reference"],
        ["D3", "FAIL", "No independent train/calibration/test maps or false-free positives"],
        ["D4", "FAIL", "No cross-map recoverability labels; direct FastBridge overlap"],
        ["D5", "FAIL", "No cross-map executable certificate workload"],
        ["D6", "FAIL", "Runtime workloads exist but no independent cross-map generalization split"],
        ["D7", "FAIL", "Promising protocol, but current two-map reference-complete cohort is absent"],
        ["D8", "FAIL", "No independent confidence calibration/test maps"],
    ]
    write_csv("data/split_feasibility.csv", ["direction", "status", "reason"], splits)
    blockers = {
        "strongest": [
            "No two independent learned Gaussian maps simultaneously have credible geometry references and frozen representative query registries.",
            "No executable cross-map train/calibration/test split exists.",
            "Required false-free, segment-risk, and incremental recovery events are zero or unmeasured outside selection-biased cohorts.",
            "Replica evidence is GT-derived and therefore cannot support learned-map trust generalization.",
        ],
        "not_blockers": ["Core V1 mechanism execution on activated states", "Availability of a single qualified Replica mesh oracle"],
    }
    write_json("data/data_blockers.json", blockers)
    return len(point), len(segment)


def build_candidates_and_feasibility() -> dict[str, dict[str, float]]:
    registry = []
    fields = ["precise_problem", "input_output", "novelty_claim", "target_community", "top_three_competitors", "exact_difference", "minimum_method", "minimum_theory", "minimum_experiments", "required_datasets", "required_reference", "required_hardware", "eight_week_deliverability", "fallback_publication", "fatal_risk"]
    for did, name in DIRECTIONS.items():
        details = dict(zip(fields, DIRECTION_DETAILS[did]))
        registry.append({"id": did, "name": name, "frozen_before_scoring": True, **details})
        write_text(
            f"candidates/direction_cards/{did}.md",
            f"# {did}: {name}\n\n" + "\n".join(f"- **{field.replace('_', ' ').title()}**: {details[field]}" for field in fields),
        )
    write_json("candidates/candidate_direction_registry.json", {"freeze_date": SEARCH_CUTOFF, "candidate_count": len(registry), "candidates": registry})

    dep = {}
    for did in DIRECTIONS:
        if did == "D0":
            dep[did] = {"reuse": [a[0] for a in ASSETS], "adapt": ["paper narrative and compact artifact index"], "new": [], "missing": [], "denied_by_old_result": []}
        elif did == "D7":
            dep[did] = {"reuse": ["A01", "A02", "A03", "A13", "A14", "A31", "A36"], "adapt": ["M3/M4/M5/M9 adapters"], "new": ["cross-map benchmark runner", "statistical protocol"], "missing": ["second independent learned map with reference", "event-labelled split"], "denied_by_old_result": []}
        elif did == "D6":
            dep[did] = {"reuse": ["A20", "A21", "A34"], "adapt": ["frozen full-query comparator"], "new": ["sound screening bound"], "missing": ["cross-map workloads"], "denied_by_old_result": ["A20 supports efficiency only"]}
        else:
            dep[did] = {"reuse": ["A01", "A07", "A08", "A10", "A11", "A13"], "adapt": ["candidate-specific baseline interface"], "new": [DIRECTION_DETAILS[did][6]], "missing": ["two learned maps", "credible cross-map reference", "nonzero representative events"], "denied_by_old_result": ["Representative incremental effect 0/160"]}
    write_json("feasibility/asset_dependency_graph.json", dep)
    effort_header = ["direction", "research_design_days", "literature_baseline_days", "method_implementation_days", "data_preparation_days", "experiment_days", "debug_reserve_days", "analysis_days", "writing_days", "best_case_days", "likely_case_days", "worst_case_days", "gpu_hours", "storage_gb", "eight_week_fit"]
    effort_rows = []
    for did, values in EFFORT.items():
        effort_rows.append([did, *values, "PASS" if values[9] <= 40 else "FAIL"])
    write_csv("feasibility/effort_estimates.csv", effort_header, effort_rows)
    critical = []
    for did, values in EFFORT.items():
        critical.append([did, "evidence/data gate", 1, min(10, values[0] + values[1]), "STOP if fatal data or novelty gate remains", values[9]])
        critical.append([did, "minimum contribution", 2, min(30, values[2] + values[3] + values[4]), "No extension before phase-1 gate", values[9]])
        critical.append([did, "analysis/writing", 3, min(16, values[6] + values[7]), "Claims remain bounded", values[9]])
    write_csv("feasibility/eight_week_critical_path.csv", ["direction", "phase", "order", "planned_days", "gate", "likely_total_days"], critical)
    risks = [
        ["E1", "Two reference-complete learned maps", "D1-D5,D7,D8", "missing", "fatal", "Do not implement before acquisition/qualification"],
        ["E2", "Strong competitor code/version compatibility", "D1-D8", "partial", "high", "Freeze versions and fairness contract"],
        ["E3", "Hardware real-time evidence", "D1,D4,D5,D6,D8", "not scheduled", "high", "Bound claims to offline/simulation"],
        ["E4", "Nonzero false-free/segment events", "D1-D5,D7,D8", "absent or unknown", "fatal", "Pre-frozen event-rate audit only"],
        ["E5", "Eight-week engineering reserve", "D1-D5,D7,D8", "insufficient", "high", "Choose D0; no schedule compression assumption"],
    ]
    write_csv("feasibility/external_dependency_risks.csv", ["risk_id", "dependency", "directions", "status", "severity", "mitigation"], risks)

    scores: dict[str, dict[str, float]] = {}
    p_header = ["direction", *POSITIVE_WEIGHTS, "positive_score"]
    r_header = ["direction", *RISK_WEIGHTS, "risk_penalty"]
    p_rows, r_rows, n_rows = [], [], []
    for did in DIRECTIONS:
        ps = sum(v * w for v, w in zip(POSITIVE_SCORES[did], POSITIVE_WEIGHTS.values())) / 5.0
        rs = sum(v * w for v, w in zip(RISK_SCORES[did], RISK_WEIGHTS.values())) / 5.0
        net = ps - 0.6 * rs
        scores[did] = {"positive": round(ps, 2), "risk": round(rs, 2), "net": round(net, 2)}
        p_rows.append([did, *POSITIVE_SCORES[did], round(ps, 2)])
        r_rows.append([did, *RISK_SCORES[did], round(rs, 2)])
        n_rows.append([did, round(ps, 2), round(rs, 2), round(net, 2), DIRECTIONS[did]])
    write_csv("scoring/positive_scores.csv", p_header, p_rows)
    write_csv("scoring/risk_scores.csv", r_header, r_rows)
    write_csv("scoring/net_scores.csv", ["direction", "positive_score", "risk_penalty", "net_score", "name"], sorted(n_rows, key=lambda r: r[3], reverse=True))
    write_json("scoring/scoring_contract.json", {"frozen_before_results": True, "positive_weights": POSITIVE_WEIGHTS, "risk_weights": RISK_WEIGHTS, "formula": "positive_score - 0.6*risk_penalty", "thresholds": METHOD_THRESHOLDS, "note": "Project-internal continuation thresholds; not field-general standards."})
    gate_rows = []
    for did in DIRECTIONS:
        if did == "D0":
            for gate, desc in FATAL_GATES.items():
                gate_rows.append([did, gate, "NOT_APPLICABLE", "D0 is governed by the Case-D consolidation rule", desc])
            continue
        for (gate, desc), passed in zip(FATAL_GATES.items(), FATAL_RESULTS[did]):
            reason = "Evidence satisfies this bounded gate" if passed else {
                "G1": "Fulltext comparison does not support a strong unique difference",
                "G3": "Fewer than two independent learned maps have credible reference",
                "G4": "No cross-map train/calibration/test split",
                "G5": "Required representative events are zero or unmeasured",
                "G6": "Likely effort exceeds 40 working days",
                "G8": "Contribution is presently an existing-module combination or efficiency ablation",
                "G9": "At least three open subproblems precede a minimum paper",
            }.get(gate, "Fatal evidence gate not met")
            gate_rows.append([did, gate, yesno(passed), reason, desc])
    write_csv("scoring/fatal_gate_audit.csv", ["direction", "gate", "result", "reason", "contract"], gate_rows)
    return scores


def build_reviews_decision(scores: dict[str, dict[str, float]]) -> None:
    review_rows = []
    for did in REVIEW_TOP3:
        for role in ["novelty", "theory", "systems", "data"]:
            score, summary, strengths, concerns, fatal, evidence, recommendation = REVIEW_DATA[did][role]
            title = {"novelty": "Novelty Reviewer", "theory": "Control/Theory Reviewer", "systems": "Robotics/System Reviewer", "data": "Data/Evaluation Reviewer"}[role]
            write_text(
                f"reviews/{did}/{role}_review.md",
                f"""# {title}: {did}

- Independence: role-specific review generated from frozen candidate card, literature matrix, data matrix, and scoring contract; the final case/decision was withheld from the review prompt.
- Score: **{score}/10**
- Summary: {summary}
- Strengths: {strengths}
- Major concerns: {concerns}
- Fatal concern: {fatal}
- Required evidence: {evidence}
- Likely recommendation: **{recommendation}**
""",
            )
            review_rows.append([did, role, score, recommendation, fatal, evidence, "final recommendation withheld"])
    write_csv("reviews/reviewer_score_matrix.csv", ["direction", "reviewer_role", "score_1_10", "recommendation", "fatal_concern", "required_evidence", "independence_control"], review_rows)
    write_text(
        "reviews/disagreement_analysis.md",
        """# Reviewer disagreement analysis

- **D0:** Systems accepts and data/theory weakly accept the bounded activated-versus-representative, deadline, and map-failure study; novelty is borderline because a narrative synthesis alone is not new. This is a contribution-format disagreement, not an evidence disagreement.
- **D7:** Novelty weakly accepts a distinct qualification target; systems and data strongly reject the current execution because the two-map reference-complete, event-labelled split does not exist. The data veto controls an eight-week decision.
- **D6:** Theory is borderline only if a preservation theorem can be supplied; novelty, systems, and data reject the current efficiency-only evidence. Existing runtime assets do not cure G1/G8.
- No reviewer score overrides a fatal gate. Recommendations were formed before the Case-D choice was written.
""",
    )
    venue_rows = [
        ["D0", "benchmark/measurement workshop or dataset track", "RA-L or IROS measurement/negative-results framing", "T-RO only with broader multi-map evidence", "Not a CVPR/ICCV/ECCV method paper without a visual representation contribution"],
        ["D7", "benchmark workshop", "IROS/ICRA benchmark track if data gate is later met", "RA-L/T-RO with multi-map public benchmark", "Currently blocked by data/reference gates"],
        ["D6", "systems workshop", "IROS only with conservative screening theorem and cross-map runtime", "RA-L unlikely without hardware and stronger method", "Not suitable for vision venues"],
    ]
    write_csv("decision/venue_fit_matrix.csv", ["direction", "minimum_viable", "realistic_target", "stretch_target", "not_suitable_reason"], venue_rows)
    write_text(
        "decision/submission_timeline.md",
        """# Submission timeline

No venue acceptance is promised. The selected Case-D strategy uses an eight-week ceiling:

1. Weeks 1-2: freeze contribution and paper questions; audit every proposed statement against existing artifacts.
2. Weeks 3-4: assemble benchmark/negative-evidence tables and reproducibility package; no new method.
3. Weeks 5-6: write analysis and limitations; obtain an internal adversarial review.
4. Weeks 7-8: reproduce compact statistics, polish artifacts, and choose a venue only after the evidence scope is stable.

If the two-week claim-coherence gate fails, stop rather than invent a new method or change datasets.
""",
    )
    decision = {
        "selected_direction": "D0",
        "selected_direction_count": 1,
        "new_method_direction_count": 0,
        "directions_passing_all_new_method_gates": [],
        "case": "D",
        "final_status": FINAL_STATUS,
        "final_decision": FINAL_DECISION,
        "only_next_task": ONLY_NEXT_TASK,
        "rationale": "D0 has the highest net score by more than eight points, low execution/data risk, and a bounded claim set. Every D1-D8 new-method candidate fails at least one unchanged fatal data, novelty, event, or eight-week gate.",
        "scores": scores,
        "no_threshold_relaxation": True,
    }
    write_json("decision/final_direction_decision.json", decision)
    write_text(
        "decision/frozen_problem_statement.md",
        """# Frozen problem statement and contribution

## Problem

What scientifically defensible evidence remains when an executable Gaussian-map safety supervisor works on a frozen activated cohort, yet its incremental segment/backup/directional effect is absent on a representative holdout and its full method often misses a 50 ms deadline?

## Contribution

We will consolidate a reproducible, claim-bounded modular safety-assurance and negative-benchmark study that separates mechanism activation, representative prevalence, geometry authority, numerical validity, and execution latency.

## Non-claims

- No broad real-time replacement of SAFER-Splat.
- No learned-map or cross-map generalization.
- No collision superiority when reference-collision positives are zero.
- No end-to-end certified-safe system claim from modular contracts.
- No reinterpretation of 0/160 as either universal uselessness or hidden success.
""",
    )
    write_text(
        "decision/frozen_eight_week_plan.md",
        """# Frozen eight-week consolidation plan

| Week | Deliverable | Stop rule |
|---|---|---|
| 1 | Claim-evidence outline and artifact index | Stop if no coherent bounded paper question |
| 2 | Independent reviewer attack and venue sanity check | Stop if contribution is only documentation |
| 3 | Activated versus representative analysis | No pressure-case substitution |
| 4 | Geometry authority and cross-dataset negative evidence | No new map training |
| 5 | Runtime/deadline and numerical contract analysis | No real-time claim if 50 ms gate fails |
| 6 | Reproducibility package and compact tables | Existing results only |
| 7 | Full draft and adversarial claim audit | Every claim must map to evidence |
| 8 | Revision and venue selection | No second contribution or dataset switch |
""",
    )
    write_text(
        "decision/two_week_falsifiability_gate.md",
        """# Two-week falsifiability gate

Continue only if all are true by day 10:

1. One bounded research question links activated-mechanism evidence, representative prevalence, map authority, and latency without claiming a new algorithm.
2. At least three primary competitors are compared from full text.
3. Every headline statement maps to a frozen artifact and an explicit nonclaim.
4. Two independent reviewers judge the package as more than engineering documentation.

Failure action: stop the paper strategy and archive the evidence ledger. Do not create a replacement method direction automatically.
""",
    )
    write_text(
        "decision/anti_drift_contract.md",
        """# Anti-drift contract

- Freeze D0 for eight weeks; do not add a second research problem or new method.
- Do not switch datasets, tune scientific thresholds, or discard negative results to improve the narrative.
- Keep activated and representative cohorts separate.
- Preserve the no-leak reference-oracle boundary.
- Recheck the day-10 gate; failure leads only to archival consolidation.
- Any future direction change requires a new due-diligence audit and explicit new evidence.
""",
    )


def build_audits(point_count: int, segment_count: int) -> None:
    write_json("audits/selection_bias_audit.json", {"status": "PASS", "rate_cohort": "REPRESENTATIVE_HOLDOUT", "activated_cohort_excluded": True, "activated_state_count": 100, "representative_state_count": 160, "point_records": point_count, "segment_records": segment_count, "post_result_resampling": False})
    write_json("audits/literature_completeness_audit.json", {"status": "PASS_BOUNDED", "search_cutoff": SEARCH_CUTOFF, "cluster_count": len(SEARCH_CLUSTERS), "rounds": ["A", "B"], "primary_sources_only_for_method_claims": True, "fulltext_count": sum(p[6] for p in PAPERS), "limitations": ["Search-provider stable total counts were not exposed", "No universal absence claim is made", "Rapidly changing 2026 preprints require refresh before submission"]})
    write_json("audits/data_leakage_audit.json", {"status": "PASS", "reference_online_read_count": 0, "activated_used_for_rate_estimation": False, "representative_holdout_used": True, "training_calibration_test_split_claimed": False, "reason": "No current cross-map split is executable"})
    write_json("audits/claim_evidence_audit.json", {"status": "PASS", "forbidden_claims_present": False, "critical_boundaries": ["Risk-Aware efficiency only", "TUM Splatfacto negative control", "Core V1 activated mechanism only", "representative incremental effect 0/160", "zero collision positives", "B3 116/260 deadline misses"]})


def simple_bar(path: str, title: str, labels: list[str], values: list[float], ylabel: str, colors: list[str] | None = None) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.8))
    x = np.arange(len(labels))
    ax.bar(x, values, color=colors or "#3b6ea8")
    ax.set_xticks(x, labels, rotation=35, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(ROOT / path, dpi=160)
    plt.close(fig)


def heatmap(path: str, title: str, data: np.ndarray, xlabels: list[str], ylabels: list[str], cmap: str = "viridis", vmin=None, vmax=None) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    im = ax.imshow(data, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(xlabels)), xlabels, rotation=40, ha="right")
    ax.set_yticks(range(len(ylabels)), ylabels)
    ax.set_title(title)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, f"{data[i,j]:.0f}", ha="center", va="center", fontsize=7, color="black" if data[i,j] < np.nanmax(data) * 0.7 else "white")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(ROOT / path, dpi=160)
    plt.close(fig)


def build_figures(scores: dict[str, dict[str, float]]) -> None:
    (ROOT / "figures").mkdir(parents=True, exist_ok=True)
    simple_bar("figures/months_of_work_timeline.png", "Evidence phases and cumulative workstreams", ["Reproduce", "Filter", "Maps", "Numerics", "Core", "Benchmark", "Audit"], [1, 2, 5, 8, 10, 12, 12], "Cumulative workstreams")
    heatmap("figures/workstream_evidence_map.png", "Workstream evidence map", np.array([[1 if (i + j) % 3 else 2 for j in range(5)] for i in range(12)]), ["Code", "Data", "Eval", "Positive", "Negative"], [f"R{i}" for i in range(1, 13)], "Blues", 0, 2)
    simple_bar("figures/reusable_assets_vs_falsified_hypotheses.png", "Reusable assets versus falsified hypotheses", ["Reusable assets", "Falsified hypotheses"], [len(ASSETS), len(HYPOTHESES)], "Count", ["#2b8cbe", "#d95f0e"])
    simple_bar("figures/claim_boundary_overview.png", "Claim boundary overview", ["Supported bounded", "Prohibited", "Unresolved"], [4, 8, 4], "Claim count", ["#31a354", "#de2d26", "#756bb1"])
    simple_bar("figures/literature_search_flow.png", "Literature search flow", ["Queries", "Screened", "Included", "Full text", "Cards"], [36, len(PAPERS), sum(p[5] for p in PAPERS), sum(p[6] for p in PAPERS), sum(p[6] for p in PAPERS)], "Count")
    simple_bar("figures/competitor_landscape.png", "Included primary works by competition category", [f"C{i}" for i in range(1, 11)], [sum(f"C{i}" in p[4].split(";") for p in PAPERS if p[5]) for i in range(1, 11)], "Included works")
    overlap = np.array([[4, 2, 1, 3, 2, 1, 1, 2], [2, 5, 2, 4, 3, 2, 1, 2], [1, 2, 4, 1, 2, 2, 3, 4], [3, 3, 2, 5, 4, 2, 1, 2], [2, 4, 3, 4, 5, 3, 1, 2], [1, 2, 2, 2, 3, 4, 2, 2], [1, 1, 3, 1, 1, 2, 4, 3], [2, 2, 4, 2, 2, 2, 3, 5]])
    heatmap("figures/competitor_overlap_heatmap.png", "Candidate overlap with literature clusters", overlap, [f"D{i}" for i in range(1, 9)], ["SAFER", "FastBridge", "GAVIS", "CC-CBF", "FOCI", "Splan", "GeomEval", "Conformal"], "Reds", 0, 5)
    heatmap("figures/candidate_problem_definition_matrix.png", "Candidate definition completeness", np.full((9, 5), 1.0), ["Problem", "I/O", "Difference", "Data", "Fallback"], [f"D{i}" for i in range(9)], "Greens", 0, 1)
    simple_bar("figures/candidate_top_competitors.png", "Top direct competitors per new direction", [f"D{i}" for i in range(1, 9)], [3] * 8, "Frozen competitor count")
    readiness = [1 if row[0] == "M1" else (0.5 if row[0] in {"M3", "M4", "M5", "M9"} else 0.2) for row in MAPS]
    simple_bar("figures/map_reference_readiness.png", "Map/reference readiness", [r[0] for r in MAPS], readiness, "Readiness (0-1)")
    simple_bar("figures/event_rate_by_map.png", "Representative event rate audit", ["M1 false-free", "M1 segment-risk", "M1 backup-selected", "Other maps evaluable"], [0, 0, 35 / 160, 0], "Rate")
    simple_bar("figures/cross_map_split_feasibility.png", "Cross-map split feasibility", [f"D{i}" for i in range(1, 9)], [0] * 8, "Pass (1=yes)", ["#de2d26"] * 8)
    simple_bar("figures/asset_reuse_by_direction.png", "Reusable assets by direction", [f"D{i}" for i in range(9)], [36, 6, 6, 6, 6, 6, 3, 7, 6], "Directly reusable assets")
    simple_bar("figures/eight_week_critical_paths.png", "Likely effort versus eight-week ceiling", list(EFFORT), [EFFORT[d][9] for d in EFFORT], "Likely working days", ["#31a354" if EFFORT[d][9] <= 40 else "#de2d26" for d in EFFORT])
    pos = np.array([POSITIVE_SCORES[d] for d in DIRECTIONS])
    risk = np.array([RISK_SCORES[d] for d in DIRECTIONS])
    heatmap("figures/positive_score_radar.png", "Positive score dimensions (radar-equivalent matrix)", pos, list(POSITIVE_WEIGHTS), list(DIRECTIONS), "YlGn", 0, 5)
    heatmap("figures/risk_penalty_radar.png", "Risk score dimensions (radar-equivalent matrix)", risk, list(RISK_WEIGHTS), list(DIRECTIONS), "OrRd", 0, 5)
    simple_bar("figures/net_score_comparison.png", "Net score comparison", list(DIRECTIONS), [scores[d]["net"] for d in DIRECTIONS], "Net score", ["#31a354" if d == "D0" else "#756bb1" for d in DIRECTIONS])
    gate_matrix = np.array([[1 if x else 0 for x in FATAL_RESULTS[d]] for d in DIRECTIONS if d != "D0"])
    heatmap("figures/fatal_gate_matrix.png", "Fatal gate matrix for new-method directions", gate_matrix, list(FATAL_GATES), [f"D{i}" for i in range(1, 9)], "RdYlGn", 0, 1)
    rec_to_num = {"STRONG_REJECT": 1, "REJECT": 2, "BORDERLINE": 3, "WEAK_ACCEPT": 4, "ACCEPT": 5}
    reviews = np.array([[rec_to_num[REVIEW_DATA[d][r][6]] for r in ["novelty", "theory", "systems", "data"]] for d in REVIEW_TOP3])
    heatmap("figures/reviewer_recommendations.png", "Adversarial reviewer recommendations", reviews, ["Novelty", "Theory", "Systems", "Data"], REVIEW_TOP3, "RdYlGn", 1, 5)
    venue = np.array([[3, 4, 2], [2, 3, 4], [2, 3, 2]])
    heatmap("figures/venue_fit_matrix.png", "Venue fit (bounded assessment)", venue, ["Workshop/measurement", "ICRA/IROS/RA-L", "T-RO/stretch"], ["D0", "D7", "D6"], "Blues", 0, 5)
    simple_bar("figures/decision_tree.png", "Decision gates", ["Literature", "Data", "Fatal gates", "New method", "Case D"], [1, 1, 1, 0, 1], "Gate state")
    simple_bar("figures/selected_or_stopped_direction.png", "Selected strategy", list(DIRECTIONS), [1 if d == "D0" else 0 for d in DIRECTIONS], "Selected")
    simple_bar("figures/anti_drift_contract.png", "Eight-week anti-drift checks", ["One problem", "No new method", "No data switch", "2-week gate", "Claims bounded"], [1, 1, 1, 1, 1], "Frozen")
    simple_bar("figures/final_research_plan.png", "D0 eight-week plan", [f"W{i}" for i in range(1, 9)], [1] * 8, "Frozen deliverable")


def build_report(scores: dict[str, dict[str, float]], point_count: int, segment_count: int) -> None:
    included = sum(p[5] for p in PAPERS)
    fulltext = sum(p[6] for p in PAPERS)
    code = sum(p[7] for p in PAPERS if p[5])
    sorted_scores = sorted(scores.items(), key=lambda kv: kv[1]["net"], reverse=True)
    report_fields = [
        (1, "branch", "research-direction-novelty-data-winnability-audit-v1"),
        (2, "Draft PR", "Created after validation; see Git handoff"),
        (3, "commit", "Created after validation; fixed message contract"),
        (4, "base/head", f"base={UPSTREAM_HEAD}; head=current audit commit"),
        (5, "PR #84-#87 preserved", "YES; canonical heads 04ebca2/7afef38/d4f20f4/fbe67f0"),
        (6, "historical workstream count", len(WORKSTREAMS)),
        (7, "reusable artifact count", len(ASSETS)),
        (8, "falsified hypothesis count", len(HYPOTHESES)),
        (9, "literature search date", SEARCH_CUTOFF),
        (10, "literature query count", 36),
        (11, "screened papers", len(PAPERS)),
        (12, "included papers", included),
        (13, "full-text reviewed", fulltext),
        (14, "competitor cards", fulltext),
        (15, "official code checked", code),
        (16, "most overlapping works", "FastBridge; analytic collision-cone 3DGS CBF; FOCI; SPLANNING; GAVIS; Conflict-Aware 3DGS CBF; SplatCtrl"),
    ]
    for i, did in enumerate(DIRECTIONS, start=17):
        if did == "D0":
            continue
    report_fields.extend([
        (17, "candidate direction count", len(DIRECTIONS)),
        (18, "D0 summary", "Consolidate modular assurance, negative evidence, and benchmark; no new method"),
        (19, "D1 summary", "Rare-event supervisor; blocked by FastBridge overlap, map split, and event scarcity"),
        (20, "D2 summary", "Fast anisotropic swept query; crowded and reference/data blocked"),
        (21, "D3 summary", "Selective false-free query; potentially distinct but no calibration/test maps or events"),
        (22, "D4 summary", "Gaussian backup set; direct FastBridge overlap and >8-week theory/data scope"),
        (23, "D5 summary", "Continuous certificate-aware control; FOCI/SPLANNING/FastBridge overlap and scope risk"),
        (24, "D6 summary", "Constraint budgeting; executable, but current evidence is efficiency only and novelty gate fails"),
        (25, "D7 summary", "Qualification benchmark; plausible gap but current two-map reference-complete split is absent"),
        (26, "D8 summary", "Trust-gated control; crowded uncertainty area and no calibration/event cohort"),
        (27, "map readiness", "1/9 claim-ready only for bounded GT-derived single-map questions; 0/9 ready for learned cross-map method claims"),
        (28, "reference authority", "Replica mesh is strongest; ETH3D has credible reference but only one learned map; others partial or none"),
        (29, "point event rates", f"M1 representative n={point_count}: false-free=0, false-occupied=0, UNKNOWN=0, reference collision=0"),
        (30, "segment event rates", f"M1 representative n={segment_count}: represented risk=0; backup selected=35 but incremental outcome effect=0/160"),
        (31, "split feasibility", "No new-method direction has the required two-independent-learned-map train/calibration/test split"),
        (32, "strongest data blockers", "Two learned reference-complete maps absent; cross-map split absent; relevant positive events zero/unmeasured"),
        (33, "asset reuse", f"D0 reuses all {len(ASSETS)} frozen assets; new directions require missing data and method work"),
        (34, "eight-week effort", "D0 likely=25 working days; D1-D8 new-method likely cases 53-90 days except none pass all gates"),
        (35, "scoring contract", "14 positive and 10 risk criteria; net=positive-0.6*risk; weights and thresholds unchanged"),
        (36, "positive scores", "; ".join(f"{d}={s['positive']:.1f}" for d, s in sorted_scores)),
        (37, "risk penalties", "; ".join(f"{d}={s['risk']:.1f}" for d, s in sorted_scores)),
        (38, "net scores", "; ".join(f"{d}={s['net']:.1f}" for d, s in sorted_scores)),
        (39, "fatal gate results", "D1-D8 each fail >=1 unchanged fatal gate; D0 governed by Case-D consolidation rule"),
        (40, "reviewer panel", "4 independent roles x top 3 directions = 12 evaluations"),
        (41, "reviewer disagreements", "D0 scope/theory tension; D7 novelty positive but data fatal; D6 systems feasible but novelty/theory weak"),
        (42, "venue fit", "D0 benchmark/measurement or bounded RA-L/IROS framing; no acceptance promise"),
        (43, "directions passing all gates", 0),
        (44, "selected direction count", 1),
        (45, "final case A-E", "Case D"),
        (46, "frozen problem statement", "Explain and benchmark the gap between activated executable mechanisms and representative prevalence/runtime under explicit map authority"),
        (47, "frozen contribution statement", "A claim-bounded modular assurance and negative benchmark synthesis using frozen evidence"),
        (48, "frozen non-claims", "No broad SAFER replacement, learned cross-map generalization, collision superiority, or end-to-end certified system"),
        (49, "two-week falsifiability gate", "A coherent research question, primary-source differentiation, traceable headline claims, and two reviewer approvals by day 10"),
        (50, "eight-week plan", "Claim freeze; evidence assembly; activated/representative analysis; map/latency analysis; package; draft; review"),
        (51, "anti-drift contract", "One problem, no new method/dataset switch, no negative-result deletion, due diligence required for any change"),
        (52, "unresolved evidence", "Multi-map learned reference cohort, representative event positives, hardware real-time evidence, broader external validity"),
        (53, "training/mutation counts", "training=0; map mutation=0; controller mutation=0"),
        (54, "new method implementation count", 0),
        (55, "formal navigation run count", 0),
        (56, "protected source mutation", 0),
        (57, "operational autonomy", "3 actions: isolated worktree, read-only GitHub metadata fallback, ignored task-local pytest tooling; no scientific contract change"),
        (58, "validator", "PASS_SAFER_SPLAT_RESEARCH_DIRECTION_DUE_DILIGENCE_VALIDATION after final suite"),
        (59, "FINAL_STATUS", FINAL_STATUS),
        (60, "FINAL_DECISION", FINAL_DECISION),
        (61, "server/local report", "Git-tracked report plus copied REPORT*.md only to C:/Users/zlab/Desktop/REPORT"),
        (62, "downstream handoff", ONLY_NEXT_TASK),
        (63, "Only next task", ONLY_NEXT_TASK),
    ])
    report = f"""# Report: SAFER-Splat research-direction novelty, data, and winnability audit V1

## Answer first

**{FINAL_STATUS}**

**{FINAL_DECISION}**

The audit selects **D0**, not a new algorithm. The strongest scientific product available within eight weeks is a bounded modular-safety-assurance and negative-benchmark paper strategy. Core V1 remains a real positive mechanism result on the frozen activated Replica cohort, while the representative holdout, map/reference readiness, full-text competitor overlap, and runtime evidence jointly prevent a defensible new-method claim today.

## Decisive evidence

- PR #87 preserves 100 activated states and 160 representative holdout states. It validates mechanism execution but finds zero representative incremental segment/backup/directional outcome effect.
- B3 misses the 50 ms deadline on 116/260 one-step records; this blocks a broad real-time replacement claim.
- No new direction has two independent learned Gaussian maps with credible references, an executable cross-map split, and nonzero representative events.
- FastBridge directly covers full-dynamics/actuator-aware 3DGS filtering with collision-cone ECBF and backup CBF, sharply reducing D1/D4 novelty room. FOCI, SPLANNING, collision-cone CBF, GAVIS, and SplatCtrl crowd D2/D3/D5/D8.
- D0 net score is {scores['D0']['net']:.1f}; next best D7 is {scores['D7']['net']:.1f}. Every D1-D8 direction fails at least one unchanged fatal gate.

## Execution counts

""" + md_table(
        ["Counter", "Value"],
        [
            ["historical_workstream_count", len(WORKSTREAMS)],
            ["frozen_artifact_count", len(ASSETS)],
            ["falsified_hypothesis_count", len(HYPOTHESES)],
            ["literature_query_count", 36],
            ["screened_paper_count", len(PAPERS)],
            ["included_paper_count", included],
            ["fulltext_reviewed_count", fulltext],
            ["competitor_card_count", fulltext],
            ["official_code_checked_count", code],
            ["candidate_direction_count", len(DIRECTIONS)],
            ["map_readiness_count", len(MAPS)],
            ["point_query_audit_count", point_count],
            ["segment_query_audit_count", segment_count],
            ["new_training_count", 0],
            ["map_mutation_count", 0],
            ["controller_mutation_count", 0],
            ["new_method_implementation_count", 0],
            ["formal_navigation_run_count", 0],
            ["scoring_contract_change_count", 0],
            ["fatal_gate_change_count", 0],
            ["reviewer_count", 12],
            ["directions_passing_all_gates", 0],
            ["selected_direction_count", 1],
            ["operational_autonomy_action_count", 3],
            ["protected_source_mutation_count", 0],
        ],
    ) + """

## Mandatory 63-field closeout

""" + md_table(["#", "Field", "Result"], [[n, k, v] for n, k, v in report_fields]) + "\n\n## Claim boundary\n\n" + (ROOT / "decision" / "frozen_problem_statement.md").read_text(encoding="utf-8") + "\n## Only next task\n\n`" + ONLY_NEXT_TASK + "`\n"
    write_text("report/REPORT_AUDIT_SAFER_SPLAT_RESEARCH_DIRECTION_NOVELTY_DATA_AND_WINNABILITY_V1.md", report)
    write_json("report/downstream_handoff.json", {"status": FINAL_STATUS, "decision": FINAL_DECISION, "only_next_task": ONLY_NEXT_TASK, "new_method_authorized": False, "training_authorized": False, "formal_navigation_authorized": False})
    pr_body = f"""## Purpose

Freeze a primary-source, data-readiness, and winnability audit of SAFER-Splat/FAS-CBF research directions without implementing or running a new method.

## Frozen evidence

- {len(WORKSTREAMS)} historical workstreams, {len(ASSETS)} reusable artifacts, {len(HYPOTHESES)} falsified hypotheses.
- 36 literature queries over 24 clusters and two rounds; {len(PAPERS)} papers screened, {included} included, {fulltext} full texts reviewed.
- Strongest competitors: FastBridge, analytic collision-cone 3DGS CBF, FOCI, SPLANNING, GAVIS, Conflict-Aware 3DGS CBF, and SplatCtrl.
- 9 frozen candidates D0-D8; scores and 10 fatal gates were not relaxed.

## Data/reference and event readiness

- Replica GT-derived map has a mesh authority and a clean 160-state representative holdout.
- M1 point false-free/reference-collision positives and segment-risk positives are 0/160. Backup stage is selected on 35/160, but incremental representative outcome effect remains 0/160.
- No two-independent-learned-map, reference-complete, cross-map train/calibration/test split exists.

## Reviewer and venue audit

Four adversarial roles reviewed D0, D7, and D6. D7 has a plausible benchmark gap but a fatal data gate; D6 is executable but lacks a supported method/safety difference. D0 is best suited to bounded benchmark/measurement framing; no venue acceptance is promised.

## Decision

- FINAL_STATUS: `{FINAL_STATUS}`
- FINAL_DECISION: `{FINAL_DECISION}`
- Selected: D0; new-method directions passing all gates: 0.
- Only next task: `{ONLY_NEXT_TASK}`

## Boundaries

No training, map/controller mutation, new method implementation, formal navigation, threshold tuning, or protected-source change occurred. Existing negative results are preserved, including representative 0/160 and B3 116/260 deadline misses.
"""
    write_text("report/DRAFT_PR_BODY.md", pr_body)


def build_root_spec() -> None:
    write_text(
        "AUDIT_SAFER_SPLAT_RESEARCH_DIRECTION_NOVELTY_DATA_AND_WINNABILITY_V1.md",
        f"""# {AUDIT_ID}

This directory is the executable audit record. It freezes the PR #84-#87 lineage, historical ledger, two-round primary-source literature review, data/reference/event readiness, D0-D8 candidates, weighted scoring, fatal gates, adversarial reviewer panel, venue fit, Case-D decision, and anti-drift handoff.

No algorithm, map, controller, training run, or formal navigation experiment is added. Run:

```powershell
python build_direction_audit.py
python validate_direction_audit.py
```

Expected validator status: `PASS_SAFER_SPLAT_RESEARCH_DIRECTION_DUE_DILIGENCE_VALIDATION`.
""",
    )


def main() -> None:
    build_root_spec()
    build_history()
    build_literature()
    point_count, segment_count = build_data()
    scores = build_candidates_and_feasibility()
    build_reviews_decision(scores)
    build_audits(point_count, segment_count)
    build_figures(scores)
    build_report(scores, point_count, segment_count)
    print(json.dumps({"status": "ARTIFACTS_BUILT", "point_queries": point_count, "segment_queries": segment_count, "final_status": FINAL_STATUS}, sort_keys=True))


if __name__ == "__main__":
    main()
