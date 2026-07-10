#!/usr/bin/env python3
"""Statically audit the local dependency closure used by the V4-C runner."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


TARGET_MODULES = (
    "run_v4c_hstep_predictive_recovery",
    "run_risk_aware_v1_pre_cbf_comparison",
    "run_v4b_corrective_dt_filter",
)
HELPER_ALIASES = {
    "v1": "run_risk_aware_v1_pre_cbf_comparison",
    "v4b": "run_v4b_corrective_dt_filter",
}
DIRECT_FIELDS = (
    "source_module",
    "imported_module",
    "import_type",
    "resolved_repo_path",
    "stdlib",
    "third_party",
    "local_module",
    "exists_in_target_branch",
    "exists_in_priority1_source",
    "required_for_import",
    "notes",
)
SYMBOL_FIELDS = (
    "consumer_module",
    "provider_module",
    "symbol",
    "usage_count",
    "usage_locations",
    "symbol_exists_in_source",
    "symbol_exists_after_restoration",
    "semantic_role",
    "required_for_shadow_m2",
    "notes",
)
TRANSITIVE_FIELDS = (
    "module_name",
    "expected_repo_path",
    "imported_by",
    "source_exists",
    "target_exists",
    "source_sha256",
    "git_tracked_at_source",
    "required_for_module_import",
    "required_for_v4c_shadow",
    "required_only_for_cli_or_reporting",
    "restoration_candidate",
    "decision",
    "reason",
    "notes",
)


def write_csv(path: Path, fields: Iterable[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def module_file(root: Path, scripts_dir: Path, module: str) -> Path | None:
    parts = module.split(".")
    candidates = (
        scripts_dir.joinpath(*parts).with_suffix(".py"),
        root.joinpath(*parts).with_suffix(".py"),
        root.joinpath(*parts, "__init__.py"),
    )
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def expected_module_path(root: Path, scripts_dir: Path, module: str) -> Path:
    local = module_file(root, scripts_dir, module)
    if local is not None:
        return local
    if module.startswith("run_"):
        return scripts_dir / f"{module}.py"
    return root.joinpath(*module.split(".")).with_suffix(".py")


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def imports_for(tree: ast.Module) -> list[tuple[str, str, int]]:
    rows: list[tuple[str, str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            rows.extend((item.name, "import", node.lineno) for item in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            rows.append((module, "from_import", node.lineno))
    return rows


def top_level_definitions(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


def semantic_role(symbol: str) -> str:
    if symbol in {"query_h", "query_h_and_critical"}:
        return "GSplat ellipsoid safety query"
    if symbol in {"clamp_control", "unit_or_zero", "parse_csv_floats"}:
        return "candidate construction helper"
    if symbol in {"make_start_goal_configs", "start_for_trial"}:
        return "official trial context construction"
    if symbol in {"nominal_control", "make_cbf", "RiskScoreTable"}:
        return "baseline control construction"
    if symbol in {"cuda_sync"}:
        return "runtime synchronization"
    if symbol in {"CsvAppender", "Logger", "read_rows", "write_csv", "json_ready"}:
        return "CLI or compact reporting support"
    if symbol.startswith("parse_") or symbol in {"bool_csv", "mean", "percentile"}:
        return "serialization or aggregation support"
    return "V4-C runner helper symbol"


def top_level_call_notes(tree: ast.Module) -> str:
    calls: list[str] = []
    for node in tree.body:
        candidates: list[ast.Call] = []
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            candidates.append(node.value)
        elif isinstance(node, ast.If):
            for child in node.body:
                if isinstance(child, ast.Expr) and isinstance(child.value, ast.Call):
                    candidates.append(child.value)
        for call in candidates:
            calls.append(f"line {call.lineno}: {ast.unparse(call.func)}")
    return "; ".join(calls) if calls else "none"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--priority-source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    root = args.repo_root.resolve()
    scripts_dir = root / "work/risk_aware_cbf/scripts"
    source_scripts = args.priority_source_root.resolve()
    output_dir = args.output_dir.resolve()
    trees: dict[str, ast.Module] = {}
    target_paths: dict[str, Path] = {}
    source_paths: dict[str, Path] = {}
    for module in TARGET_MODULES:
        target = scripts_dir / f"{module}.py"
        source = source_scripts / f"{module}.py"
        path = target if target.is_file() else source
        if not path.is_file():
            raise FileNotFoundError(f"missing analysis target: {module}")
        trees[module] = parse_module(path)
        target_paths[module] = target
        source_paths[module] = source

    direct_rows: list[dict[str, Any]] = []
    importers: dict[str, set[str]] = defaultdict(set)
    for source_module, tree in trees.items():
        notes = top_level_call_notes(tree)
        for imported, import_type, line in imports_for(tree):
            base = imported.lstrip(".").split(".")[0]
            resolved = module_file(root, scripts_dir, imported.lstrip("."))
            expected = expected_module_path(root, scripts_dir, imported.lstrip("."))
            source_expected = source_scripts / f"{base}.py"
            is_stdlib = base in sys.stdlib_module_names or base == "__future__"
            is_local = resolved is not None or source_expected.is_file() or base.startswith("run_")
            is_third_party = not is_stdlib and not is_local
            importers[imported.lstrip(".")].add(source_module)
            direct_rows.append(
                {
                    "source_module": source_module,
                    "imported_module": imported,
                    "import_type": import_type,
                    "resolved_repo_path": str((resolved or expected).relative_to(root)).replace("\\", "/"),
                    "stdlib": bool_text(is_stdlib),
                    "third_party": bool_text(is_third_party),
                    "local_module": bool_text(is_local),
                    "exists_in_target_branch": bool_text(expected.is_file()),
                    "exists_in_priority1_source": bool_text(source_expected.is_file() or expected.is_file()),
                    "required_for_import": "true",
                    "notes": f"import line {line}; top-level calls: {notes}",
                }
            )

    provider_defs = {
        module: top_level_definitions(tree) for module, tree in trees.items()
    }
    usages: dict[tuple[str, str], list[int]] = defaultdict(list)
    runner_tree = trees["run_v4c_hstep_predictive_recovery"]
    for node in ast.walk(runner_tree):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in HELPER_ALIASES
        ):
            usages[(node.value.id, node.attr)].append(node.lineno)
    symbol_rows: list[dict[str, Any]] = []
    for (alias, symbol), lines in sorted(usages.items()):
        provider = HELPER_ALIASES[alias]
        exists_source = symbol in provider_defs.get(provider, set())
        provider_target = target_paths[provider]
        exists_target = provider_target.is_file() and exists_source
        symbol_rows.append(
            {
                "consumer_module": "run_v4c_hstep_predictive_recovery",
                "provider_module": provider,
                "symbol": symbol,
                "usage_count": len(lines),
                "usage_locations": ";".join(str(line) for line in sorted(lines)),
                "symbol_exists_in_source": bool_text(exists_source),
                "symbol_exists_after_restoration": bool_text(exists_target),
                "semantic_role": semantic_role(symbol),
                "required_for_shadow_m2": "true",
                "notes": "Derived from AST attribute references; not a hand-maintained symbol list.",
            }
        )

    transitive_rows: list[dict[str, Any]] = []
    unique_imports = sorted(importers)
    for module in unique_imports:
        base = module.split(".")[0]
        is_stdlib = base in sys.stdlib_module_names or base == "__future__"
        resolved = module_file(root, scripts_dir, module)
        expected = expected_module_path(root, scripts_dir, module)
        source_file = source_scripts / f"{base}.py"
        is_local = resolved is not None or source_file.is_file() or base.startswith("run_")
        is_third_party = not is_stdlib and not is_local
        if is_stdlib:
            decision = "stdlib"
            reason = "Python standard library"
        elif is_third_party:
            decision = "third_party_dependency"
            reason = "Environment dependency; never copied into repository"
        elif expected.is_file():
            decision = "already_present"
            reason = "Required local module already exists in target branch"
        elif source_file.is_file():
            decision = "restore_exact"
            reason = "Required import-time local module exists in Priority-1 source"
        else:
            decision = "blocked_missing"
            reason = "Required local import is missing from source and target"
        reporting_only = module in {"matplotlib", "matplotlib.pyplot", "pandas"}
        transitive_rows.append(
            {
                "module_name": module,
                "expected_repo_path": str(expected.relative_to(root)).replace("\\", "/"),
                "imported_by": ";".join(sorted(importers[module])),
                "source_exists": bool_text(source_file.is_file() or expected.is_file()),
                "target_exists": bool_text(expected.is_file()),
                "source_sha256": sha256(source_file) if source_file.is_file() else "",
                "git_tracked_at_source": "false" if source_file.is_file() and base.startswith("run_") else "not_measured",
                "required_for_module_import": "true",
                "required_for_v4c_shadow": bool_text(not reporting_only),
                "required_only_for_cli_or_reporting": bool_text(reporting_only),
                "restoration_candidate": bool_text(decision == "restore_exact"),
                "decision": decision,
                "reason": reason,
                "notes": "Static AST dependency classification.",
            }
        )

    write_csv(output_dir / "direct_import_graph.csv", DIRECT_FIELDS, direct_rows)
    write_csv(output_dir / "required_symbol_inventory.csv", SYMBOL_FIELDS, symbol_rows)
    write_csv(
        output_dir / "transitive_dependency_inventory.csv",
        TRANSITIVE_FIELDS,
        transitive_rows,
    )
    counts = Counter(row["decision"] for row in transitive_rows)
    print(
        f"imports={len(direct_rows)} symbols={len(symbol_rows)} "
        f"restore_exact={counts['restore_exact']} blocked_missing={counts['blocked_missing']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
