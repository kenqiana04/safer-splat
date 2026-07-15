#!/usr/bin/env python3
"""Collect immutable Git/source evidence for Experiment Protocol Freeze V1."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reproduction" / "experiment_protocol_freeze_v1"
COMMITS = {
    "safc_method_redesign_analysis": "4ef0ac7601c2eae91adc1f319ede288071d13999",
    "r1_supervisory_mode_shadow_audit": "4f2eb3f4cbe2184da2fcf2264288c7cdefa3d88e",
    "v4c_interface_restoration": "b626b99cb1ed1437730c0e0734635fd8f0bdc517",
    "v4c_helper_dependency_closure": "fc3e942c1ab957c910785fdeefae57f537ef3a9f",
    "v4c_module_failure_analysis": "e8b2485c4494812b7d4c3b55fb185c5c68b2096a",
    "v4c_hierarchical_candidate_evaluation_v0": "11e2a4f8c49266a11c4c178e947b46ee70612d99",
    "v4c_hierarchical_heldout_activated_cohort": "a83259798e0e4b1a2c7fcdce2617ebd8783ebcc3",
    "v4c_trial20_recovery_failure_diagnosis": "4f8e00fcc10cbeb98b933d3507eb009659e1341f",
    "v4c_gtep_shadow_feasibility": "41ccb54d2e9f10c0b3b559431a58a5763977d462",
}
EVIDENCE = {
    "run.py": ("baseline", "scene/checkpoint dispatch"),
    "splat/gsplat_utils.py": ("barrier_geometry", "repository GSplat ellipsoid safety field"),
    "work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py": ("v4c", "predictive recovery wrapper"),
    "work/risk_aware_cbf/scripts/run_v4c_hierarchical_paired_audit.py": ("hce", "development paired contract"),
    "work/risk_aware_cbf/scripts/run_v4c_hierarchical_heldout_active_ab.py": ("hce", "held-out active protocol"),
    "work/risk_aware_cbf/scripts/run_v4c_trial20_failure_diagnosis.py": ("trial20", "targeted recovery diagnosis"),
    "work/risk_aware_cbf/scripts/run_v4c_gtep_shadow_audit.py": ("gtep", "geometry-conditioned shadow diagnostic"),
    "work/risk_aware_cbf/REPORT_STARTGUARD_FLIGHT100.md": ("startguard", "original/post-repair separation"),
    "work/risk_aware_cbf/REPORT_RISK_AWARE_V1_FLIGHT_100_TRIAL.md": ("risk_aware_v1", "flight100 evidence"),
    "work/risk_aware_cbf/REPORT_V4C_FLIGHT100_VALIDATION.md": ("v4c", "full100 H3/N128 evidence"),
    "work/risk_aware_cbf/REPORT_V4C_HIERARCHICAL_HELDOUT_ACTIVATED_COHORT.md": ("hce", "held-out cohort evidence"),
    "work/risk_aware_cbf/REPORT_V4C_TRIAL20_RECOVERY_FAILURE_DIAGNOSIS.md": ("trial20", "failure boundary"),
    "work/risk_aware_cbf/REPORT_V4C_GTEP_SHADOW_FEASIBILITY.md": ("gtep", "negative diagnostic"),
    "work/risk_aware_cbf/results/v4c_hierarchical_heldout_activated_cohort/heldout_cohort_preregistration.csv": ("hce", "held-out trial registry"),
    "work/risk_aware_cbf/results/v4c_hierarchical_heldout_activated_cohort/run_order_preregistration.csv": ("hce", "execution order registry"),
    "work/risk_aware_cbf/results/v4c_trial20_failure_diagnosis/preregistration.csv": ("trial20", "trial20 frozen comparator"),
    "work/risk_aware_cbf/results/v4c_gtep_shadow_audit/trial20_context_preregistration.csv": ("gtep", "ordered trial20 contexts"),
}


def git(*args: str) -> tuple[int, str]:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    (OUT / "provenance").mkdir(parents=True, exist_ok=True)
    head = git("rev-parse", "HEAD")[1]
    entries = []
    for name, commit in COMMITS.items():
        typ_code, typ = git("cat-file", "-t", commit)
        stat_code, stat = git("show", "--stat", "--oneline", "--no-renames", commit)
        ancestor_code, _ = git("merge-base", "--is-ancestor", commit, "HEAD")
        entries.append({"module": name, "commit": commit, "object_type": typ if typ_code == 0 else "missing", "reachable_from_freeze_parent": ancestor_code == 0, "show_stat": stat if stat_code == 0 else "unavailable"})
    (OUT / "provenance" / "commit_reachability.json").write_text(json.dumps({"freeze_parent": head, "commits": entries}, indent=2) + "\n", encoding="utf-8")

    fields = ["path", "type", "size_bytes", "sha256", "git_tracked", "last_commit", "match_module", "evidence_role", "read_status"]
    with (OUT / "provenance" / "source_file_inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for relative, (module, role) in EVIDENCE.items():
            path = ROOT / relative
            tracked = git("ls-files", "--error-unmatch", relative)[0] == 0
            last = git("log", "-1", "--format=%H", "--", relative)[1] if path.exists() else ""
            writer.writerow({"path": relative, "type": path.suffix.lstrip(".") if path.exists() else "missing", "size_bytes": path.stat().st_size if path.exists() else "", "sha256": sha256(path) if path.is_file() else "", "git_tracked": str(tracked).lower(), "last_commit": last, "match_module": module, "evidence_role": role, "read_status": "read" if path.is_file() else "unresolved_missing"})


if __name__ == "__main__":
    main()
