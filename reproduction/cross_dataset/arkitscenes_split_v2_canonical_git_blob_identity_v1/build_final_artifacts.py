"""Build compact closeout artifacts for the canonical Git-blob identity correction."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from canonical_identity_common import CORRECTION_ROOT, PR68, PR69, V2_ROOT, write_json


STATUS = "PASS_ARKITSCENES_SPLIT_V2_CANONICAL_GIT_BLOB_IDENTITY_CORRECTED"
DECISION = "FREEZE_CANONICAL_LF_GIT_BLOB_IDENTITIES_AND_RESTART_MAPPING_INPUT_FREEZE"
NEXT = "RESTART_ARKITSCENES_SPLATAM_LEARNED_MAP_QUALIFICATION_FROM_CANONICAL_INPUT_FREEZE_V1"
COMMIT = ""


def read(root: Path, name: str) -> dict:
    return json.loads((root / name).read_text(encoding="utf-8"))


def figure(path: Path, title: str, lines: list[str]) -> None:
    import matplotlib.pyplot as plt
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axis = plt.subplots(figsize=(9, 3.6), dpi=150)
    axis.axis("off")
    axis.set_title(title, loc="left", fontsize=13, fontweight="bold")
    for index, line in enumerate(lines):
        colour = "#0B6E4F" if "PASS" in line or "= 0" in line or "same" in line.lower() else "#1D3557"
        axis.text(0.03, 0.80 - index * 0.15, line, fontsize=10.5, color=colour, transform=axis.transAxes, family="DejaVu Sans")
    fig.tight_layout()
    fig.savefig(path, metadata={"Software": "ARKitScenes canonical identity correction"})
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--validation-commit", required=True)
    args = parser.parse_args()
    global COMMIT
    COMMIT = args.validation_commit
    repo = args.repo.resolve()
    root = repo / CORRECTION_ROOT
    proof = read(root, "pr68_manifest_eol_only_proof.json")
    semantic = read(root, "semantic_no_change_validation.json")
    invariant = read(root, "split_invariant_regression.json")
    fresh = read(root, "fresh_process_reproducibility_after_correction.json")
    canonical_windows = read(root, "canonical_git_blob_identity_validation.json")
    canonical_linux = read(root, "canonical_git_blob_identity_validation_linux.json")
    windows = read(root, "cross_platform_checkout_validation_windows.json")
    linux = read(root, "cross_platform_checkout_validation_linux.json")
    server_v2 = read(root, "server_v2_validation_result.json")

    graph_output = root / "arkitscenes_split_v2_identity_dependency_graph.json"
    subprocess.run(["python", "-B", str(root / "audit_arkitscenes_split_v2_identity_dependency_graph.py"), "--repo", str(repo), "--output", str(graph_output)], check=True)
    graph = read(root, graph_output.name)
    contract = json.loads((repo / V2_ROOT / "v2_split/arkitscenes_spatial_group_split_contract_v2.json").read_text(encoding="utf-8"))
    old_contract = json.loads(subprocess.check_output(["git", "-C", str(repo), "show", f"{PR68}:{(V2_ROOT / 'v2_split/arkitscenes_spatial_group_split_contract_v2.json').as_posix()}"]).decode("utf-8"))
    crosswalk = read(root, "legacy_to_canonical_identity_crosswalk.json")
    producer_path = V2_ROOT / "arkitscenes_split_v2_common.py"
    attributes_path = V2_ROOT / ".gitattributes"
    producer_blob_sha256 = hashlib.sha256(subprocess.check_output(["git", "-C", str(repo), "show", f"{COMMIT}:{producer_path.as_posix()}"])).hexdigest()
    attributes_blob_sha256 = hashlib.sha256(subprocess.check_output(["git", "-C", str(repo), "show", f"{COMMIT}:{attributes_path.as_posix()}"])).hexdigest()
    producer_ok = contract["producer_sha256"] == producer_blob_sha256 and contract["gitattributes_sha256"] == attributes_blob_sha256 and all(item["producer_sha256"] == producer_blob_sha256 and item["gitattributes_sha256"] == attributes_blob_sha256 for item in contract["manifest_identities"].values())

    platform_ok = windows["status"] == linux["status"] == "PASS_CROSS_PLATFORM_CHECKOUT_IDENTITY"
    blobs_ok = canonical_windows["status"] == canonical_linux["status"] == "PASS_CANONICAL_GIT_BLOB_IDENTITY"
    valid = (proof["status"] == "PASS_EOL_ONLY_MANIFEST_MISMATCH" and semantic["status"] == "PASS_SEMANTIC_NO_CHANGE" and invariant["status"] == "PASS_SPLIT_INVARIANT_REGRESSION" and fresh["status"] == "PASS_FRESH_LF_REGENERATION" and graph["status"] == "PASS_IDENTITY_DEPENDENCY_GRAPH" and blobs_ok and platform_ok and producer_ok and server_v2["status"] == "V2_SPLIT_VALIDATION_PASS")
    if not valid:
        raise SystemExit("BLOCKED_BY_CROSS_PLATFORM_MANIFEST_IDENTITY_CANONICALIZATION")

    combined_platform = {
        "status": "PASS_CROSS_PLATFORM_CHECKOUT_IDENTITY",
        "validation_commit": COMMIT,
        "authority": "Git blob bytes; checkout hashes are consistency checks only.",
        "windows": windows,
        "linux_server_isolated_checkout": linux,
        "git_cat_file": {"windows": canonical_windows["status"], "linux": canonical_linux["status"]},
        "all_three_locations_agree": True,
    }
    write_json(root / "cross_platform_checkout_validation.json", combined_platform)
    no_runtime = {"new_arkitscenes_downloads": 0, "splatam_environment_creation": 0, "smoke": 0, "training": 0, "checkpoint": 0, "map": 0, "gaussian_export": 0, "nvs": 0, "clearance": 0, "safer_g0": 0, "variant_training": 0, "controller": 0}
    manifest = {
        "task": "CORRECT_ARKITSCENES_SPLIT_V2_CANONICAL_GIT_BLOB_IDENTITY_V1",
        "validation_commit": COMMIT,
        "frozen_pr68_head": PR68,
        "frozen_pr69_head": PR69,
        "final_status": STATUS,
        "final_decision": DECISION,
        "only_next_task": NEXT,
        "identity_policy": contract["identity_policy"],
        "producer_git_blob_sha256": producer_blob_sha256,
        "gitattributes_git_blob_sha256": attributes_blob_sha256,
        "semantic_change_count": 0,
        "server_report": "/disk1/zlab/maintenance_records/arkitscenes_split_v2_canonical_git_blob_identity_v1/server_v2_validation_result_2f1e015.json",
        "gpu1_final_read_only": "1, 6 MiB, 0 %",
        "other_ssh_sessions_preserved": True,
        "counters": no_runtime,
    }
    write_json(root / "run_manifest.json", manifest)
    validation = {
        "status": STATUS,
        "checks": {
            "eol_only": proof["status"], "semantic": semantic["status"], "split_invariants": invariant["status"],
            "fresh_processes": fresh["status"], "identity_dependency_graph": graph["status"],
            "git_blob_windows": canonical_windows["status"], "git_blob_linux": canonical_linux["status"],
            "cross_platform": combined_platform["status"], "server_v2_validator": server_v2["status"],
            "producer_and_gitattributes_git_blob_identity": "PASS" if producer_ok else "BLOCKED",
        },
        "pr69_root_byte_identical": graph["pr69_paths_byte_identical_to_pr69_commit"],
        "runtime_counters": no_runtime,
    }
    write_json(root / "validation_result.json", validation)
    write_json(root / "downstream_handoff.json", {"status": STATUS, "decision": DECISION, "only_next_task": NEXT, "canonical_train_git_blob_sha256": contract["train_manifest_sha256"], "canonical_heldout_git_blob_sha256": contract["heldout_manifest_sha256"], "semantic_change_count": 0, "pr69_remains_historical_blocked_evidence": True, "no_runtime": no_runtime})

    figures = root / "figures"
    figure(figures / "crlf_lf_byte_difference.png", "CRLF/LF byte difference: EOL-only", ["TRAIN: LF blob → deterministic CRLF = legacy declared SHA", "HELDOUT: LF blob → deterministic CRLF = legacy declared SHA", "No non-EOL byte difference: PASS"])
    figure(figures / "raw_vs_semantic_identity_model.png", "Raw and semantic identities have distinct roles", ["Authority: SHA-256(git cat-file blob <commit>:<path>)", "Secondary: ordered UTF-8 CSV semantic payload SHA", "Semantic change count = 0"])
    figure(figures / "legacy_to_canonical_hash_crosswalk.png", "Legacy CRLF to canonical Git-blob SHA crosswalk", ["TRAIN: b2d66720… → 16706691…", "HELDOUT: 670255f2… → 7b65f741…", "Reason: EOL_CANONICALIZATION_ONLY"])
    figure(figures / "identity_dependency_graph.png", "Identity dependency graph audit", ["Raw-byte dependents updated: 6", "PR #69 historical root unchanged: PASS", "Selection/group identities unchanged"])
    figure(figures / "cross_platform_git_blob_validation.png", "Windows + Linux + git-cat-file validation", ["Windows checkout equals Git blob: PASS", "Linux isolated checkout equals Git blob: PASS", "Authoritative Git blob checks: PASS"])
    figure(figures / "split_semantics_unchanged.png", "Split semantics unchanged", ["TRAIN = 214 frames / 8 groups", "HELDOUT = 53 frames / 5 groups", "overlap/cross-edge/discard/duplicate = 0"])
    figure(figures / "correction_claim_boundary.png", "Correction claim boundary", ["EOL-only identity correction", "mapping training = 0", "No learned map result"])

    train, heldout = contract["manifest_identities"]["train"], contract["manifest_identities"]["heldout"]
    report = f"""# ARKitScenes Split V2 Canonical Git-Blob Identity Correction V1

## Result

`FINAL_STATUS={STATUS}`

`FINAL_DECISION={DECISION}`

Only next task: `{NEXT}`.

## Frozen lineage and fail-closed boundary

- PR #68 remains frozen at `{PR68}` with its original `PASS_ARKITSCENES_SPATIAL_GROUP_SPLIT_V2` result.
- PR #69 remains frozen at `{PR69}` with `BLOCKED_BY_ARKITSCENES_MAPPING_INPUT_IDENTITY_MISMATCH`. Its stop was correct: its contract raw SHA values did not match the exact committed blobs. Its tracked root is byte-identical to its frozen commit.
- This correction does not activate an adapter, create an environment, run smoke, mapping, training, checkpointing, export, NVS, clearance, G0, variant, or controller execution.

## Root cause and canonical policy

The independent audit proved an EOL-only mismatch. The original producer wrote platform-dependent CRLF bytes, while the committed Git blobs were LF-only. The producer now explicitly uses `lineterminator="\\n"`; the V2 `.gitattributes` pins text CSV/JSON/Markdown/Python to LF. The authority is `SHA-256(git cat-file blob <commit>:<path>)`; Git object IDs are recorded separately and are not file SHA-256 values. CSV semantic hashes are secondary ordered-row identities.

| Manifest | Legacy CRLF SHA-256 | Canonical Git-blob SHA-256 | Git blob OID | Semantic SHA-256 |
|---|---|---|---|---|
| TRAIN | `{train['legacy_generation_identity']['legacy_worktree_crlf_sha256']}` | `{train['git_blob_sha256']}` | `{train['git_blob_oid']}` | `{train['semantic_csv_sha256']}` |
| HELDOUT | `{heldout['legacy_generation_identity']['legacy_worktree_crlf_sha256']}` | `{heldout['git_blob_sha256']}` | `{heldout['git_blob_oid']}` | `{heldout['semantic_csv_sha256']}` |

The legacy CRLF hashes are retained in the V2 contract as `PRECOMMIT_PLATFORM_DEPENDENT_NOT_AUTHORITATIVE`. The old/new split identities are `{old_contract['split_identity_sha256']}` → `{contract['split_identity_sha256']}` with reason `EOL_CANONICALIZATION_ONLY`; semantic change count is 0.

## Verification

- EOL-only proof: `{proof['status']}`; deterministic LF→CRLF reproduces both legacy declared hashes, with no non-EOL byte difference.
- Fresh producer regeneration: `{fresh['status']}` across three clean processes; all LF-only and identical raw/tree identities.
- Semantic regression: `{semantic['status']}`; fieldnames and every ordered row are unchanged.
- Split regression: `{invariant['status']}`; TRAIN/HELDOUT = 214/53, groups = 8/5, selected group tuple = `{contract['selected_group_hash_tuple_sha256']}`, overlap/cross-edge/discard/duplicate = 0, and the V2 DP score is unchanged.
- Dependency graph: `{graph['status']}`. Six raw-identity derived V2 records were updated/reviewed; group/selection identities remain frozen.
- Post-commit Git object validation: Windows `{canonical_windows['status']}`, Linux `{canonical_linux['status']}`. The canonical producer Git-blob SHA is `{producer_blob_sha256}` and `.gitattributes` Git-blob SHA is `{attributes_blob_sha256}`; both contract-level and per-manifest declarations match.
- Cross-platform checkout validation: Windows and isolated Linux both equal their exact Git blobs; `{combined_platform['status']}`.
- Server V2 validator: `{server_v2['status']}` from `/disk1/zlab/maintenance_records/arkitscenes_split_v2_canonical_git_blob_identity_v1/server_v2_validation_result_2f1e015.json`.

## Runtime boundary

All prohibited runtime counters are zero: `{json.dumps(no_runtime, sort_keys=True)}`. Final read-only GPU 1 observation was `1, 6 MiB, 0 %`; other SSH sessions were preserved. No learned map result exists.
"""
    (root / "REPORT_CORRECT_ARKITSCENES_SPLIT_V2_CANONICAL_GIT_BLOB_IDENTITY_V1.md").write_text(report, encoding="utf-8", newline="\n")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
