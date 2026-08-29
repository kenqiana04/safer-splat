#!/usr/bin/env python3
"""Serial fail-closed orchestration for the preregistered A/B/C matrix."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from arm_activation_validator import validate as validate_activation
from compare_traces import compare


ARMS = {"A": "NATIVE_OFF", "B": "WRAPPER_OFF", "C": "WRAPPER_ON"}
SELECTION = (0, 24, 49, 74, 99)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def command_text(command: list[str]) -> str:
    return " ".join(command)


class Pipeline:
    def __init__(self, *, checkout: Path, task_code: Path, output_root: Path, python: Path) -> None:
        self.checkout = checkout.resolve(strict=True)
        self.task_code = task_code.resolve(strict=True)
        self.output_root = output_root.resolve()
        self.python = python.resolve(strict=True)
        self.output_root.mkdir(parents=True, exist_ok=False)
        for name in ("runs", "run_logs", "traces", "comparisons"):
            (self.output_root / name).mkdir()
        self.run_records: list[dict[str, Any]] = []
        self.comparisons: list[dict[str, Any]] = []
        self.first_divergence: dict[str, Any] | None = None
        self.final_case = "UNRESOLVED"
        self.final_status = "UNRESOLVED"
        self.final_decision = "UNRESOLVED"
        self.only_next_task = "UNRESOLVED"

    def diagnostic(self) -> dict[str, Any]:
        commands = {
            "gpu": ["nvidia-smi", "-i", "1", "--query-gpu=index,name,memory.used,utilization.gpu", "--format=csv,noheader"],
            "compute": ["nvidia-smi", "-i", "1", "--query-compute-apps=pid,process_name,used_gpu_memory", "--format=csv,noheader"],
            "process": ["pgrep", "-af", str(self.output_root)],
        }
        result = {}
        for name, command in commands.items():
            completed = subprocess.run(command, text=True, capture_output=True, check=False)
            result[name] = {"returncode": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}
        return result

    def run_one(self, arm: str, trial_id: int, label: str, *, retry: int = 0) -> dict[str, Any]:
        run_id = f"{label.lower()}_trial{trial_id:03d}" + ("" if retry == 0 else f"_retry{retry}")
        run_dir = self.output_root / "runs" / run_id
        before = self.diagnostic()
        command = [
            str(self.python), "-B", str(self.task_code / "server_run_one.py"),
            "--arm", arm, "--trial-id", str(trial_id), "--seed", "0",
            "--run-id", run_id, "--checkout", str(self.checkout), "--run-dir", str(run_dir),
            "--queue-capacity", "8", "--shutdown-timeout", "120",
        ]
        env = os.environ.copy()
        env.update({
            "CUDA_VISIBLE_DEVICES": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
            "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
        })
        completed = subprocess.run(command, cwd=self.checkout, env=env, text=True, capture_output=True, check=False)
        (self.output_root / "run_logs" / f"{run_id}.stdout.log").write_text(completed.stdout, encoding="utf-8", newline="\n")
        (self.output_root / "run_logs" / f"{run_id}.stderr.log").write_text(completed.stderr, encoding="utf-8", newline="\n")
        after = self.diagnostic()
        record = {
            "run_id": run_id,
            "arm_code": arm,
            "arm": ARMS[arm],
            "trial_id": trial_id,
            "phase_label": label,
            "retry_index": retry,
            "fresh_process": True,
            "command": command_text(command),
            "exit_code": completed.returncode,
            "gpu_process_before": before,
            "gpu_process_after": after,
            "run_dir": str(run_dir),
        }
        if (run_dir / "run_metadata.json").is_file():
            record["metadata"] = load(run_dir / "run_metadata.json")
            record["activation"] = load(run_dir / "arm_activation.json")
            record["environment"] = load(run_dir / "environment_identity.json")
            passed, failures = validate_activation(record["activation"])
            record["activation_validator_pass"] = passed
            record["activation_validator_failures"] = failures
            trace_target = self.output_root / "traces" / f"{run_id}.json"
            trace_target.write_bytes((run_dir / "primary_trace.json").read_bytes())
            record["trace_path"] = str(trace_target)
        self.run_records.append(record)
        write_json(self.output_root / "paired_run_manifest.json", {"runs": self.run_records})

        if arm == "C" and (completed.returncode != 0 or not record.get("activation_validator_pass", False)) and retry == 0:
            return self.run_one(arm, trial_id, label, retry=1)
        return record

    def paired_compare(self, left: dict[str, Any], right: dict[str, Any], pair_label: str) -> dict[str, Any]:
        left_env, right_env = left.get("environment"), right.get("environment")
        if not left_env or not right_env or left_env["pairing_identity_hash"] != right_env["pairing_identity_hash"]:
            result = {
                "pair": pair_label, "trial_id": left.get("trial_id"), "exact_match": False,
                "pairing_identity_match": False,
                "first_divergence": {"field": "pairing_identity_hash", "left": None if not left_env else left_env.get("pairing_identity_hash"), "right": None if not right_env else right_env.get("pairing_identity_hash")},
            }
        else:
            result = compare(load(Path(left["trace_path"])), load(Path(right["trace_path"])), pair_label)
            result["pairing_identity_match"] = True
        self.comparisons.append(result)
        write_json(self.output_root / "comparisons" / f"{pair_label.lower()}_{left['run_id']}_to_{right['run_id']}.json", result)
        if not result["exact_match"] and self.first_divergence is None:
            divergence = dict(result.get("first_divergence") or {})
            divergence.update({
                "left_run": left,
                "right_run": right,
                "observer_health": {
                    "left": left.get("activation"), "right": right.get("activation"),
                },
            })
            self.first_divergence = divergence
            write_json(self.output_root / "first_divergence_forensic.json", divergence)
            lines = [
                "# First divergence context", "",
                f"- pair: `{pair_label}`",
                f"- trial: `{divergence.get('trial_id')}`",
                f"- step: `{divergence.get('step_id')}`",
                f"- field: `{divergence.get('field')}`",
                "- tolerance: none; canonical exact equality",
                "- post-hoc tolerance change: false",
            ]
            (self.output_root / "first_divergence_context.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        return result

    def set_case(self, case: str) -> None:
        mapping = {
            "CASE_A": ("PASS_L2_H1_SHADOW_INSTRUMENTATION_OFF_VS_ON_EQUIVALENCE_V1", "FREEZE_RUNTIME_NONINTERFERENCE_EVIDENCE_AND_VALIDATE_LOGGING_COMPLETENESS_PILOT", "VALIDATE_L2_H1_SHADOW_LOGGING_COMPLETENESS_PILOT_V1"),
            "CASE_B": ("BLOCKED_EQUIVALENCE_BY_NATIVE_BASELINE_NONDETERMINISM", "DO_NOT_ATTRIBUTE_CROSS_ARM_DIFFERENCE", "DESIGN_NONDETERMINISM_AWARE_SHADOW_EQUIVALENCE_V1"),
            "CASE_C": ("FAIL_SHADOW_EQUIVALENCE_BY_WRAPPER_PERTURBATION", "DO_NOT_RUN_PROSPECTIVE_PILOT_AND_FIX_WRAPPER_NONINTERFERENCE", "FIX_SHADOW_WRAPPER_RUNTIME_NONINTERFERENCE_V1"),
            "CASE_D": ("FAIL_SHADOW_EQUIVALENCE_BY_OBSERVER_PERTURBATION", "DO_NOT_RUN_LOGGING_PILOT_AND_FIX_OBSERVER_RUNTIME_COUPLING", "FIX_L2_H1_SHADOW_OBSERVER_RUNTIME_COUPLING_V1"),
            "CASE_E": ("BLOCKED_EQUIVALENCE_BY_INVALID_INSTRUMENTED_RUN", "DO_NOT_RUN_LOGGING_PILOT", "FIX_L2_H1_SHADOW_RUNTIME_ACTIVATION_V1"),
            "CASE_F": ("BLOCKED_EQUIVALENCE_BY_PAIRING_IDENTITY_MISMATCH", "DO_NOT_ATTRIBUTE_CROSS_ARM_DIFFERENCE", "FIX_L2_H1_EQUIVALENCE_RUN_PAIRING_V1"),
        }
        self.final_case = case
        self.final_status, self.final_decision, self.only_next_task = mapping[case]

    def valid(self, record: dict[str, Any]) -> bool:
        return record.get("exit_code") == 0 and record.get("activation_validator_pass") is True

    def execute(self) -> int:
        self_runs: dict[str, list[dict[str, Any]]] = {arm: [] for arm in ARMS}
        for arm in ("A", "B", "C"):
            for repeat in (1, 2):
                record = self.run_one(arm, 0, f"SELF_{arm}{repeat}")
                self_runs[arm].append(record)
                if not self.valid(record):
                    self.set_case("CASE_E" if arm == "C" else "CASE_F")
                    return self.finish(self_runs)
            result = self.paired_compare(self_runs[arm][0], self_runs[arm][1], f"SELF_{arm}")
            if not result.get("pairing_identity_match", False):
                self.set_case("CASE_F")
                return self.finish(self_runs)
            if not result["exact_match"]:
                self.set_case({"A": "CASE_B", "B": "CASE_C", "C": "CASE_D"}[arm])
                return self.finish(self_runs)
            if arm == "B":
                cross = self.paired_compare(self_runs["A"][0], self_runs["B"][0], "SELF_A_VS_B")
                if not cross.get("pairing_identity_match", False):
                    self.set_case("CASE_F")
                    return self.finish(self_runs)
                if not cross["exact_match"]:
                    self.set_case("CASE_C")
                    return self.finish(self_runs)
            if arm == "C":
                cross_bc = self.paired_compare(self_runs["B"][0], self_runs["C"][0], "SELF_B_VS_C")
                cross_ac = self.paired_compare(self_runs["A"][0], self_runs["C"][0], "SELF_A_VS_C")
                if not cross_bc.get("pairing_identity_match", False) or not cross_ac.get("pairing_identity_match", False):
                    self.set_case("CASE_F")
                    return self.finish(self_runs)
                if not cross_bc["exact_match"] or not cross_ac["exact_match"]:
                    self.set_case("CASE_D")
                    return self.finish(self_runs)

        cross_runs: dict[int, dict[str, dict[str, Any]]] = {}
        for trial_id in SELECTION:
            cross_runs[trial_id] = {}
            a = self.run_one("A", trial_id, "CROSS_A")
            b = self.run_one("B", trial_id, "CROSS_B")
            cross_runs[trial_id].update({"A": a, "B": b})
            if not self.valid(a) or not self.valid(b):
                self.set_case("CASE_F")
                return self.finish(self_runs, cross_runs)
            ab = self.paired_compare(a, b, f"A_VS_B_TRIAL_{trial_id:03d}")
            if not ab.get("pairing_identity_match", False):
                self.set_case("CASE_F")
                return self.finish(self_runs, cross_runs)
            if not ab["exact_match"]:
                self.set_case("CASE_C")
                return self.finish(self_runs, cross_runs)
            c = self.run_one("C", trial_id, "CROSS_C")
            cross_runs[trial_id]["C"] = c
            if not self.valid(c):
                self.set_case("CASE_E")
                return self.finish(self_runs, cross_runs)
            bc = self.paired_compare(b, c, f"B_VS_C_TRIAL_{trial_id:03d}")
            ac = self.paired_compare(a, c, f"A_VS_C_TRIAL_{trial_id:03d}")
            if not bc.get("pairing_identity_match", False) or not ac.get("pairing_identity_match", False):
                self.set_case("CASE_F")
                return self.finish(self_runs, cross_runs)
            if not bc["exact_match"] or not ac["exact_match"]:
                self.set_case("CASE_D")
                return self.finish(self_runs, cross_runs)
        self.set_case("CASE_A")
        return self.finish(self_runs, cross_runs)

    def arm_c_sanity(self) -> dict[str, Any]:
        run_checks = []
        for record in self.run_records:
            if record["arm_code"] != "C" or record.get("exit_code") != 0:
                continue
            root = Path(record["run_dir"]) / "instrumentation"
            captures = [json.loads(line) for line in (root / "step_capture_log.jsonl").read_text(encoding="utf-8").splitlines() if line]
            results = [json.loads(line) for line in (root / "shadow_certificate_result_log.jsonl").read_text(encoding="utf-8").splitlines() if line]
            health = [json.loads(line) for line in (root / "instrumentation_health_log.jsonl").read_text(encoding="utf-8").splitlines() if line]
            map_manifest = load(root / "map_authority_manifest.json")
            capture_by = {(row["run_id"], row["trial_id"], row["step_id"], row["payload_sequence_id"]): row for row in captures}
            joined = 0
            hashes = True
            selected_present = True
            for row in results:
                key = (row["run_id"], row["trial_id"], row["step_id"], row["payload_sequence_id"])
                capture = capture_by.get(key)
                if capture is not None:
                    joined += 1
                    hashes &= capture["payload_semantic_hash"] == row["payload_enqueue_semantic_hash"] == row["payload_worker_receive_semantic_hash"]
                    selected_present &= bool(capture.get("selected_candidate", {}).get("u"))
            run_checks.append({
                "run_id": record["run_id"], "capture_count": len(captures), "result_count": len(results),
                "health_count": len(health), "joined_result_count": joined,
                "payload_hash_join": hashes, "selected_u_present": selected_present,
                "map_authority_id": map_manifest.get("map_authority_id"),
                "pass": len(captures) > 0 and len(results) > 0 and joined == len(results) and hashes and selected_present,
            })
        return {
            "schema_version": "L2_H1_SHADOW_ARM_C_MINIMAL_LOG_SANITY_V1",
            "run_count": len(run_checks),
            "runs": run_checks,
            "all_pass": bool(run_checks) and all(row["pass"] for row in run_checks),
            "logging_completeness_pilot": False,
            "prevalence_estimate": False,
        }

    def finish(self, self_runs: dict[str, list[dict[str, Any]]], cross_runs: dict[int, dict[str, dict[str, Any]]] | None = None) -> int:
        sanity = self.arm_c_sanity()
        write_json(self.output_root / "arm_c_log_sanity.json", sanity)
        if self.first_divergence is None:
            write_json(self.output_root / "first_divergence_forensic.json", {"status": "NONE", "first_divergence_count": 0})
            (self.output_root / "first_divergence_context.md").write_text("# First divergence context\n\nNONE. All executed exact comparisons matched.\n", encoding="utf-8", newline="\n")
        self_consistency = {
            arm: {
                "run_ids": [record["run_id"] for record in records],
                "valid": len(records) == 2 and all(self.valid(record) for record in records),
                "exact": any(item["pair"] == f"SELF_{arm}" and item["exact_match"] for item in self.comparisons),
            } for arm, records in self_runs.items()
        }
        write_json(self.output_root / "self_consistency_results.json", self_consistency)
        matrix_path = self.output_root / "equivalence_matrix.csv"
        with matrix_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["pair", "trial_id", "exact_match", "pairing_identity_match", "left_step_count", "right_step_count", "first_divergence_field"])
            writer.writeheader()
            for row in self.comparisons:
                writer.writerow({
                    "pair": row.get("pair"), "trial_id": row.get("trial_id"), "exact_match": row.get("exact_match"),
                    "pairing_identity_match": row.get("pairing_identity_match"), "left_step_count": row.get("left_step_count"),
                    "right_step_count": row.get("right_step_count"),
                    "first_divergence_field": None if not row.get("first_divergence") else row["first_divergence"].get("field"),
                })
        cross_complete = 0 if cross_runs is None else sum(set(arms) == {"A", "B", "C"} for arms in cross_runs.values())
        counts = {arm: sum(record["arm_code"] == arm for record in self.run_records) for arm in ARMS}
        summary = {
            "selected_case": self.final_case,
            "FINAL_STATUS": self.final_status,
            "FINAL_DECISION": self.final_decision,
            "Only_next_task": self.only_next_task,
            "real_qa_navigation_run_count": len(self.run_records),
            "native_off_run_count": counts["A"],
            "wrapper_off_run_count": counts["B"],
            "wrapper_on_run_count": counts["C"],
            "frozen_trial_ids": list(SELECTION),
            "cross_arm_complete_trial_count": cross_complete,
            "exact_comparison_count": sum(bool(item.get("exact_match")) for item in self.comparisons),
            "first_divergence_count": 0 if self.first_divergence is None else 1,
            "arm_c_log_sanity": sanity["all_pass"],
            "controller_mutation_count": 0,
            "instrumentation_mutation_count": 0,
            "controller_intervention_count": 0,
            "candidate_replacement_count": 0,
            "logging_pilot_run_count": 0,
            "formal_on_policy_cohort_count": 0,
            "formal_performance_metric_count": 0,
            "formal_runtime_metric_count": 0,
            "L3_implementation_count": 0,
            "L4_implementation_count": 0,
            "L5_implementation_count": 0,
            "H2_implementation_count": 0,
        }
        write_json(self.output_root / "equivalence_summary.json", summary)
        write_json(self.output_root / "pipeline_result.json", summary)
        write_json(self.output_root / "paired_run_manifest.json", {"runs": self.run_records, "comparisons": self.comparisons, "summary": summary})
        print(json.dumps(summary, sort_keys=True), flush=True)
        return 0 if self.final_case == "CASE_A" else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--task-code", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    args = parser.parse_args()
    return Pipeline(checkout=args.checkout, task_code=args.task_code, output_root=args.output_root, python=args.python).execute()


if __name__ == "__main__":
    raise SystemExit(main())
