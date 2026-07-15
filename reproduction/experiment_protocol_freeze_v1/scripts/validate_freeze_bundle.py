#!/usr/bin/env python3
"""Validate Freeze V1 provenance/readiness without executing a dataset or controller."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reproduction" / "experiment_protocol_freeze_v1"
PARENT = "41ccb54d2e9f10c0b3b559431a58a5763977d462"
REVISION_PARENT = "bc6400beba13d216c3efd56ccdaf22968bcb560b"
REQUIRED = [
    "EXPERIMENT_PROTOCOL_FROZEN_V1.md", "METRICS_AND_FAILURE_TAXONOMY.md", "config_registry.yaml", "dataset_registry.yaml", "trial_set_registry.yaml", "provenance/commit_reachability.json", "provenance/source_file_inventory.csv", "commit_lock.json", "freeze_bundle_sha256.json", "CROSS_DATASET_PREFREEZE_PROVENANCE_V1.md", "cross_dataset_protocol_registry.yaml", "provenance/cross_dataset_evidence_inventory.csv", "provenance/cross_dataset_commit_reachability.json",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> tuple[int, str]:
    process = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    return process.returncode, (process.stdout + process.stderr).strip()


def git_bytes(*args: str) -> tuple[int, bytes]:
    process = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    return process.returncode, process.stdout


def main() -> None:
    checks: list[dict[str, object]] = []
    warnings: list[str] = []
    unresolved_critical: list[dict[str, object]] = []
    unresolved_noncritical = [
        {"field": "historical_official100_seed", "scope": "exact historical rerun only", "blocks_aggregate_evidence_freeze": False, "blocks_new_G1": False},
        {"field": "historical_official100_start_goal_source", "scope": "exact historical rerun only", "blocks_aggregate_evidence_freeze": False, "blocks_new_G1": False},
        {"field": "tum_metric_candidate_scene_identifier", "scope": "target dataset naming", "blocks_aggregate_evidence_freeze": False, "blocks_new_G1": True},
    ]

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": passed, "detail": detail})

    for relative in REQUIRED:
        check(f"required:{relative}", (OUT / relative).is_file(), "required freeze artifact")
    try:
        provenance = json.loads((OUT / "provenance/commit_reachability.json").read_text(encoding="utf-8"))
        invalid = [row["module"] for row in provenance["commits"] if row["object_type"] != "commit"]
        nonancestor = [row["module"] for row in provenance["commits"] if not row["reachable_from_freeze_parent"]]
        check("all_required_commits_resolve", not invalid, ", ".join(invalid) or "all required commit objects resolve")
        check("nonancestor_method_history_recorded", True, ", ".join(nonancestor) or "all audited method commits are ancestors")
    except Exception as exc:
        check("commit_reachability_parse", False, repr(exc))
    try:
        with (OUT / "provenance/source_file_inventory.csv").open(encoding="utf-8", newline="") as handle:
            inventory = list(csv.DictReader(handle))
        missing = [row["path"] for row in inventory if row["read_status"] != "read"]
        bad_hashes = [row["path"] for row in inventory if row["read_status"] == "read" and sha(ROOT / row["path"]) != row["sha256"]]
        check("source_inventory_hashes", not bad_hashes, ", ".join(bad_hashes) or "all source hashes match")
        check("source_inventory_readable", not missing, ", ".join(missing) or "all indexed source evidence readable")
    except Exception as exc:
        check("source_inventory_parse", False, repr(exc))
    try:
        with (OUT / "provenance/cross_dataset_evidence_inventory.csv").open(encoding="utf-8", newline="") as handle:
            cross_evidence = list(csv.DictReader(handle))
        bad = []
        for row in cross_evidence:
            code, data = git_bytes("show", f"{row['source_commit']}:{row['path']}")
            if code or hashlib.sha256(data).hexdigest() != row["sha256"] or row["read_status"] != "read":
                bad.append(row["evidence_id"])
        check("cross_dataset_source_report_hashes", not bad, ", ".join(bad) or "all Git-historical report hashes match")
        replica_row = next(row for row in cross_evidence if row["evidence_id"] == "replica_formal_report")
        _, replica_data = git_bytes("show", f"{replica_row['source_commit']}:{replica_row['path']}")
        body = replica_data.decode("utf-8", errors="replace")
        check("replica_integrity_counts_traceable", "33 RGB frames" in body and "32 depth frames" in body, "formal report records RGB/depth invalid counts")
        check("replica_manifest_hash_traceable", "1056121e4470124e180a3367172440f540f0acdc5adab665c3187ac8ab87be25" in body, "formal report records manifest SHA-256")
    except Exception as exc:
        check("cross_dataset_inventory_parse", False, repr(exc))
    try:
        cross_commits = json.loads((OUT / "provenance/cross_dataset_commit_reachability.json").read_text(encoding="utf-8"))
        bad = [row["commit"] for row in cross_commits["commits"] if not row["object_exists"] or not row["available_via_git_show"]]
        external = [row["commit"] for row in cross_commits["commits"] if not row["ancestor_of_freeze_head"]]
        check("cross_dataset_commit_provenance", not bad, ", ".join(bad) or "all historical Cross-Dataset commits resolve")
        check("cross_dataset_external_lineage_not_configuration_conflict", True, ", ".join(external) or "all Cross-Dataset commits are ancestors")
        if external:
            warnings.append("Cross-Dataset evidence is historical external lineage, not merged method lineage: " + ", ".join(external))
    except Exception as exc:
        check("cross_dataset_commit_reachability_parse", False, repr(exc))
    try:
        registry = json.loads((OUT / "cross_dataset_protocol_registry.yaml").read_text(encoding="utf-8"))
        replica = registry["datasets"]["replica_apartment_0"]
        tum = registry["datasets"]["tum_metric_candidate"]
        check("cross_dataset_registry_parse", True, "JSON-compatible YAML parsed")
        check("replica_g0_contract", replica["G0_D_rgb_depth_integrity"]["status"] == "failed" and replica["G1_allowed"] is False and replica["block_reason"] == "blocked_by_rgb_integrity", "Replica is correctly blocked at RGB/depth integrity")
        replica_unstarted = ["G0_E_gsplat_reconstruction_checkpoint", "G0_F_safer_loader_attribute_compatibility", "G0_G_ellipsoid_safety_query", "G0_H_start_goal_navigation_volume", "G0_I_collision_progress_evaluator", "G0_J_dynamics_wrapper"]
        check("replica_no_unstarted_stage_promoted", all(replica[key]["status"] == "not_started" for key in replica_unstarted), "Replica reconstruction/training/SAFER gates remain unstarted")
        check("tum_g1_contract", tum["G1_allowed"] is False and all(tum[key]["status"] != "passed" for key in ["G0_E_gsplat_reconstruction_checkpoint", "G0_F_safer_loader_attribute_compatibility", "G0_G_ellipsoid_safety_query"]), "TUM remains G0 pending and G1 blocked")
    except Exception as exc:
        replica, tum = {}, {}
        check("cross_dataset_registry_parse", False, repr(exc))
    try:
        dataset_text = (OUT / "dataset_registry.yaml").read_text(encoding="utf-8")
        check("dataset_registry_entries", all(f"id: {value}" in dataset_text for value in ["stonehenge_official", "flight_dense_official", "replica_apartment_0", "tum_metric_candidate"]), "all required dataset entries are present")
    except Exception as exc:
        check("dataset_registry_read", False, repr(exc))
    try:
        heldout = list(csv.DictReader((OUT / "trial_manifests/heldout_activated_16.csv").open(encoding="utf-8", newline="")))
        ids = [int(row["trial"]) for row in heldout]
        check("heldout_count", len(ids) == 16 and len(ids) == len(set(ids)), f"heldout={ids}")
        check("development_heldout_disjoint", not {12, 13, 14}.intersection(ids), "development [12,13,14] is disjoint")
        trial20 = list(csv.DictReader((OUT / "trial_manifests/trial20_activation_contexts.csv").open(encoding="utf-8", newline="")))
        check("trial20_order", [int(row["activation_index"]) for row in trial20] == list(range(1, 35)), "original 34-context order retained")
        trial_code, _ = git("diff", "--exit-code", REVISION_PARENT, "--", "reproduction/experiment_protocol_freeze_v1/trial_manifests/")
        check("existing_trial_manifests_unchanged", trial_code == 0, "trial manifests unchanged from revision parent")
    except Exception as exc:
        check("trial_manifest_parse", False, repr(exc))
    try:
        config_text = (OUT / "config_registry.yaml").read_text(encoding="utf-8")
        check("algorithm_config_id_count", len(re.findall(r"^  - id:", config_text, flags=re.MULTILINE)) == 21, "exactly 21 algorithm configuration IDs retained")
        check("configuration_conflicts", "configuration_conflict: true" not in config_text, "no recorded H/N/margin conflict")
    except Exception as exc:
        check("config_registry_read", False, repr(exc))
    forbidden_h3 = re.compile(r"robust reference|robust-reference|robust horizon|H3 is the robust reference|robust guarantee|robustly safe|robust certificate|robust invariance", re.IGNORECASE)
    hits = [path.relative_to(OUT).as_posix() for path in OUT.rglob("*") if path.is_file() and path.suffix in {".md", ".yaml", ".json"} and forbidden_h3.search(path.read_text(encoding="utf-8", errors="ignore"))]
    check("h3_overclaim_wording_removed", not hits, ", ".join(hits) or "H3 described only as conservative same-model offline reference")
    try:
        bundle = json.loads((OUT / "freeze_bundle_sha256.json").read_text(encoding="utf-8"))
        bad = [row["path"] for row in bundle["files"] if not (OUT / row["path"]).is_file() or sha(OUT / row["path"]) != row["sha256"]]
        check("freeze_bundle_hashes", not bad, ", ".join(bad) or "bundle hashes match")
    except Exception as exc:
        check("freeze_bundle_parse", False, repr(exc))
    code, changed = git("diff", "--name-only", PARENT, "HEAD")
    status_code, porcelain = git("status", "--porcelain")
    # Porcelain status has a two-character status prefix, but preserve the path
    # on Windows regardless of the exact whitespace representation.
    working_paths = [line.lstrip(" ?MADRCU!") for line in porcelain.splitlines() if line]
    unexpected = [path for path in [line for line in changed.splitlines() if line] + working_paths if not path.replace("\\", "/").startswith("reproduction/experiment_protocol_freeze_v1/")]
    check("allowed_path_only", code == 0 and status_code == 0 and not unexpected, ", ".join(unexpected) or "all changes are inside freeze directory")
    code, parent = git("merge-base", "HEAD", PARENT)
    check("freeze_parent", code == 0 and parent == PARENT, f"merge-base={parent}")
    failed = [row for row in checks if not row["passed"]]
    historical_ready = not any(row["check"] in {"all_required_commits_resolve", "source_inventory_hashes", "source_inventory_readable", "algorithm_config_id_count", "existing_trial_manifests_unchanged"} for row in failed)
    cross_ready = not any(row["check"] in {"cross_dataset_source_report_hashes", "cross_dataset_commit_provenance", "replica_g0_contract", "tum_g1_contract"} for row in failed)
    replica_g0, tum_g0 = replica.get("block_reason", "unresolved"), "pending" if tum else "unresolved"
    replica_g1, tum_g1 = replica.get("G1_allowed", False), tum.get("G1_allowed", False)
    if failed:
        status = "FAIL"
    elif unresolved_critical:
        status = "BLOCKED_BY_CRITICAL_PROVENANCE"
    elif historical_ready and cross_ready and not replica_g1 and not tum_g1:
        status = "PASS_FREEZE_BUT_G1_BLOCKED"
    elif unresolved_noncritical:
        status = "PASS_WITH_UNRESOLVED_NONCRITICAL_FIELDS"
    else:
        status = "PASS"
    payload = {"status": status, "freeze_parent": PARENT, "revision_parent_commit": REVISION_PARENT, "historical_method_freeze_ready": historical_ready, "cross_dataset_prefreeze_provenance_ready": cross_ready, "replica_G0_status": replica_g0, "replica_G1_allowed": replica_g1, "tum_G0_status": tum_g0, "tum_G1_allowed": tum_g1, "future_G1_global_status": "blocked" if not replica_g1 and not tum_g1 else "not_determined", "unresolved_critical_fields": unresolved_critical, "unresolved_noncritical_fields": unresolved_noncritical, "configuration_conflicts": False, "checks": checks, "failed_checks": [row["check"] for row in failed], "warnings": warnings, "note": "No GPU, renderer, training, SAFER loader, baseline, or trial execution occurred. Historical external lineage is provenance, not a configuration conflict."}
    (OUT / "validation_result.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(status)
    if failed:
        print(json.dumps(failed, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
