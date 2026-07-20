"""Snapshot C3/R0 source from immutable Git objects and compare source semantics."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args])


def source_record(path: str, data: bytes, blob: str) -> dict[str, object]:
    text = data.decode("utf-8")
    tree = ast.parse(text)
    normalized = ast.dump(tree, annotate_fields=True, include_attributes=False)
    imports = [node.names[0].name if isinstance(node, ast.Import) else node.module for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    inventory = [node.name for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]
    return {"path": path, "git_blob_sha": blob, "sha256": hashlib.sha256(data).hexdigest(), "line_count": text.count("\n") + (bool(text) and not text.endswith("\n")), "ast_normalized_sha256": hashlib.sha256(normalized.encode()).hexdigest(), "imports": imports, "top_level_inventory": inventory}


def files_at(repo: Path, rev: str, prefix: str) -> list[str]:
    return [line for line in git(repo, "ls-tree", "-r", "--name-only", rev, "--", prefix).decode().splitlines() if line.endswith(".py")]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--pr33", required=True)
    parser.add_argument("--pr34", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    prefixes = {"pr33_exact": "reproduction/cross_dataset/tum_map_geometry_root_cause_repair_v1", "pr34_exact": "reproduction/cross_dataset/tum_metric_geometry_repair_refinement_v1"}
    snapshots: dict[str, list[dict[str, object]]] = {}
    for label, prefix in prefixes.items():
        rev = args.pr33 if label.startswith("pr33") else args.pr34
        target = args.out / label; target.mkdir(exist_ok=True)
        records = []
        for path in files_at(args.repo, rev, prefix):
            data = git(args.repo, "show", f"{rev}:{path}")
            blob = git(args.repo, "rev-parse", f"{rev}:{path}").decode().strip()
            rel = Path(path).relative_to(prefix); dest = target / rel; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)
            records.append(source_record(path, data, blob))
        snapshots[label] = records
    pr33_by_name = {Path(row["path"]).name: row for row in snapshots["pr33_exact"]}
    pr34_by_name = {Path(row["path"]).name: row for row in snapshots["pr34_exact"]}
    comparisons = []
    for name in sorted(set(pr33_by_name) | set(pr34_by_name)):
        left, right = pr33_by_name.get(name), pr34_by_name.get(name)
        if not left or not right: status, category = "only_one_protocol", "CONFIRMED_SEMANTIC"
        elif left["sha256"] == right["sha256"]: status, category = "byte_identical", "IDENTICAL"
        elif left["ast_normalized_sha256"] == right["ast_normalized_sha256"]: status, category = "format_or_comment_only", "NONSEMANTIC"
        else: status, category = "ast_divergent", "POTENTIALLY_SEMANTIC"
        comparisons.append({"basename": name, "pr33": left, "pr34": right, "status": status, "category": category})
    result = {"pr33_commit": args.pr33, "pr34_commit": args.pr34, "snapshots": snapshots, "comparisons": comparisons}
    (args.out / "source_snapshot_manifest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pr33_files": len(snapshots['pr33_exact']), "pr34_files": len(snapshots['pr34_exact']), "comparisons": len(comparisons)}, sort_keys=True))


if __name__ == "__main__":
    main()
