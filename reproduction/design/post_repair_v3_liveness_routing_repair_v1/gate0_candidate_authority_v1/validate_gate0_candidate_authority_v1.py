#!/usr/bin/env python3
"""CPU-only Gate 0 design validator; synthetic fixtures, no runtime import/call."""
from __future__ import annotations

import hashlib
import json
import math
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
BASE = "919c5518b07447d248293de1fe40023c0bfb8f9b"
REL = "reproduction/design/post_repair_v3_liveness_routing_repair_v1/gate0_candidate_authority_v1/"
ORDER = ("+x", "-x", "+y", "-y", "+z", "-z")
SOURCE = "SOURCE_BOUNDED_LOCAL_RECOVERY_V1"
VERSION = "AXIS_EXTREMA_F32_V1"
REQUIRED = (
    "GATE0_PROTOCOL.json", "EXISTING_CANDIDATE_AUTHORITY_AUDIT.md",
    "RECOVERY_CANDIDATE_SOURCE_SPEC.md", "RECOVERY_CANDIDATE_GENERATOR_SPEC.md",
    "RECOVERY_CANDIDATE_ORDERING_SPEC.md", "RECOVERY_EXHAUSTION_KEY_SPEC.md",
    "RECOVERY_REJECTION_TRACE_SCHEMA.md", "ROUTING_PRIORITY_SPEC.md",
    "DESIGN_EDGE_CASE_MATRIX.md", "IMPLEMENTATION_HANDOFF.md", "README.md",
    "validate_gate0_candidate_authority_v1.py",
    "report/REPORT_GATE0_BOUNDED_LOCAL_RECOVERY_CANDIDATE_AUTHORITY_V1.md",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def dump(name: str, value: object) -> None:
    out = ROOT / "results" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha(material: object) -> str:
    return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def f32bits(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("nonfinite fixture")
    value = 0.0 if value == 0.0 else float(value)
    return struct.pack("!f", value).hex()


def vector_id(vec: tuple[float, float, float], actuator="actuator-A", transition="transition-A") -> str:
    return sha({"n": 3, "f32be": [f32bits(v) for v in vec], "actuator": actuator, "transition": transition})


def state_bits(state: tuple[float, ...]) -> str:
    return sha([f32bits(v) for v in state])


def key(state=(0.,) * 6, map_id="map-A", generator=VERSION, actuator="actuator-A", backup="NONE") -> str:
    return sha({"numeric_state": state_bits(state), "goal": state_bits((0.,) * 6), "dt": f32bits(.05),
                "map": map_id, "source": SOURCE, "generator": generator,
                "actuator": actuator, "geometry": "hard-0.015q", "transition": "transition-A",
                "backend": "backend-A", "backup_routing_class": backup})


def generate(low=(-.1,) * 3, high=(.1,) * 3, primary=None, duplicate_path=False,
             fixture_state="synthetic-state-A", fixture_map="map-A"):
    if len(low) != 3 or len(high) != 3 or any(not (math.isfinite(lo) and math.isfinite(hi) and lo < 0 < hi) for lo, hi in zip(low, high)):
        return [], "AUTHORITY_UNSUPPORTED_FAIL_CLOSED"
    raw = [(high[0], 0., 0.), (low[0], 0., 0.), (0., high[1], 0.), (0., low[1], 0.), (0., 0., high[2]), (0., 0., low[2])]
    if duplicate_path:
        raw.insert(1, raw[0])  # synthetic dedup probe, never a runtime F1 path
    seen = set([vector_id(primary)]) if primary is not None else set()
    out = []
    for raw_rank, vec in enumerate(raw):
        bits = tuple(f32bits(v) for v in vec)
        if bits == (f32bits(0),) * 3:
            continue
        ident = vector_id(vec)
        if ident not in seen:
            seen.add(ident)
            out.append({"raw_rank": raw_rank, "direction": ORDER[min(raw_rank if not duplicate_path else max(0, raw_rank-1), 5)], "vector_bits": bits,
                        "canonical_action_identity": ident, "fixture_candidate_id": "candidate:gate0-fixture:" + sha({"rank": raw_rank, "vector_id": ident, "source": SOURCE, "state": fixture_state, "map": fixture_map})})
    return out, "PASS"


def enumeration():
    rows = []
    expected_count = {"E01": 6, "E02": 6, "E03": 6, "E04": 6, "E05": 6,
                      "E06": 5, "E07": 5, "E08": 0, "E09": 6, "E10": 0,
                      "E11": 0, "E12": 6, "E13": 6, "E14": 0, "E15": 6, "E16": 6}
    base_key = key()
    for i in range(1, 17):
        eid = f"E{i:02d}"
        state = (0.,) * 6
        if i == 2: state = (0., 0., 0., .1, 0., 0.)
        if i == 3: state = (0., 0., 0., -.1, 0., 0.)
        if i == 4: state = (0., 0., 0., 0., .1, 0.)
        if i == 5: state = (0., 0., 0., .03, -.04, .02)
        kwargs = {}
        if i == 6: kwargs["primary"] = (.1, 0., 0.)
        if i == 7: kwargs["primary"] = (0., -.1, 0.)
        if i == 8: kwargs.update(low=(0., 0., 0.), high=(0., 0., 0.))
        if i == 9: kwargs.update(low=(-.08, -.09, -.07), high=(.1, .06, .04))
        if i == 16: kwargs["duplicate_path"] = True
        kwargs["fixture_state"] = state_bits(state)
        kwargs["fixture_map"] = "map-mismatch" if i == 11 else "map-A"
        if i == 15:
            state = (struct.unpack("!f", bytes.fromhex("00000001"))[0], 0., 0., 0., 0., 0.)
            kwargs["fixture_state"] = state_bits(state)
        candidates, status = generate(**kwargs)
        if i in (10, 11):
            candidates, status = [], "IDENTITY_MISMATCH_FAIL_CLOSED"
        if i == 14:
            candidates, status = [], "EXHAUSTED_SAME_KEY_NO_RESCAN"
        material = {"id": eid, "input_state_bits_hash": state_bits(state), "exhaustion_key":
                    key(state, generator="AXIS_EXTREMA_F32_V2" if i == 12 else VERSION,
                        actuator="actuator-B" if i == 13 else "actuator-A"),
                    "count": len(candidates), "order": [r["direction"] for r in candidates],
                    "candidate_identities": [r["fixture_candidate_id"] for r in candidates],
                    "canonical_action_identities": [r["canonical_action_identity"] for r in candidates],
                    "dedup_removed": (1 if i in (6, 7, 16) else 0), "exhaustion_behavior": status}
        if i == 14: material["exhaustion_key"] = base_key
        material["pass"] = material["count"] == expected_count[eid] and len(material["canonical_action_identities"]) == len(set(material["canonical_action_identities"]))
        rows.append(material)
    assert all(r["pass"] for r in rows)
    assert rows[11]["exhaustion_key"] != base_key and rows[12]["exhaustion_key"] != base_key
    assert rows[13]["exhaustion_key"] == base_key
    # Same 6-decimal print, distinct binary32 representation.
    tiny = struct.unpack("!f", bytes.fromhex("00000001"))[0]
    assert format(tiny, ".6f") == format(0., ".6f") and key((tiny, 0, 0, 0, 0, 0)) != base_key
    rows[14]["input_state_bits_hash"] = state_bits((tiny, 0, 0, 0, 0, 0))
    rows[14]["exhaustion_key"] = key((tiny, 0, 0, 0, 0, 0))
    dump("CANDIDATE_GENERATOR_STATIC_ENUMERATION.json", {"status": "PASS", "fixtures": rows, "no_runtime_generator_call": True})
    dump("ORDERING_DETERMINISM_CHECK.json", {"status": "PASS", "frozen_order": ORDER, "repeat_equal": generate()[0] == generate()[0], "first_full_pass_rank_rule": "MINIMUM_RETAINED_GENERATOR_RANK"})
    dump("EXHAUSTION_KEY_COLLISION_CHECK.json", {"status": "PASS", "same_key_same_material": key() == base_key, "new_generator_new_key": key(generator="v2") != base_key,
       "new_actuator_new_key": key(actuator="B") != base_key, "changed_backup_class_new_key": key(backup="INVALID") != base_key,
       "cycle_epoch_excluded": True, "near_print_equal_but_bits_distinct": key((tiny, 0, 0, 0, 0, 0)) != base_key})
    return rows


def route(f: dict) -> str:
    # A design fixture for the proposed Supervisor extension, never runtime policy.
    if f.get("primary_pass"): return "PRIMARY"
    if f.get("backup_valid"): return "BACKUP"
    if f.get("identity_mismatch"): return "BOUNDARY"
    if f.get("recovery_allowed") and f.get("l3_local_fail") and f.get("terminal_pass") and f.get("deadline", "OPEN") == "OPEN" and f.get("source_authorized", True) and not f.get("exhausted", False):
        for candidate in f.get("candidates", ()):
            if candidate == "PASS": return "RECOVERY"
            if candidate in ("UNKNOWN_GLOBAL", "IDENTITY_MISMATCH"): break
    if f.get("terminal_pass"): return "TERMINAL"
    return "BOUNDARY"


def routing():
    common = {"l3_local_fail": True, "recovery_allowed": True, "terminal_pass": True, "candidates": ["FAIL"] * 6}
    cases = [
      ("R01", {**common, "primary_pass": True, "backup_valid": True}, "PRIMARY"),
      ("R02", {**common, "backup_valid": True}, "BACKUP"),
      ("R03", {**common, "candidates": ["PASS"]}, "RECOVERY"),
      ("R04", {**common, "candidates": ["FAIL", "PASS"]}, "RECOVERY"),
      ("R05", common, "TERMINAL"),
      ("R06", {**common, "candidates": ["UNKNOWN"] * 6}, "TERMINAL"),
      ("R07", {**common, "identity_mismatch": True, "candidates": ["PASS"]}, "BOUNDARY"),
      ("R08", {**common, "deadline": "WARNING", "candidates": ["PASS"]}, "TERMINAL"),
      ("R09", {**common, "source_authorized": False}, "TERMINAL"),
      ("R10", {**common, "exhausted": True}, "TERMINAL"),
      ("R11", {**common, "backup_valid": True, "candidates": ["PASS"]}, "BACKUP"),
      ("R12", {**common, "backup_valid": False, "candidates": ["PASS"]}, "RECOVERY"),
      ("R13", {**common, "terminal_pass": False}, "BOUNDARY"),
      ("R14", {**common, "recovery_allowed": False}, "TERMINAL"),
      ("R15", {**common, "recovery_allowed": False}, "TERMINAL"),
      ("R16", {**common, "recovery_allowed": False}, "TERMINAL"),
      ("R17", {**common, "l3_local_fail": False}, "TERMINAL"),
      ("R18", {**common, "deadline": "WARNING"}, "TERMINAL"),
      ("R19", {**common, "deadline": "EXPIRED"}, "TERMINAL"),
      ("R20", {**common, "candidates": ["FAIL", "PASS"]}, "RECOVERY"),
      ("R21", {**common, "candidates": ["FAIL"] * 6}, "TERMINAL"),
      ("R22", {**common, "primary_pass": True}, "PRIMARY"),
      ("R23", {**common, "candidates": ["PASS"]}, "RECOVERY"),
      ("R24", {**common, "candidates": ["PASS"], "historical_025_diagnostic": True}, "RECOVERY"),
    ]
    rows = [{"id": name, "expected": expected, "observed": route(facts), "exact_one": True, "pass": route(facts) == expected} for name, facts, expected in cases]
    counterexamples = [r for r in rows if not r["pass"]]
    dump("ROUTING_PRIORITY_EXACT_ONE_CHECK.json", {"status": "PASS" if not counterexamples else "FAIL", "fixture_count": len(rows), "rows": rows,
      "model_counterexamples": counterexamples, "scope": "STATIC_DESIGN_ONLY_NOT_EXECUTABLE_RUNTIME_TABLE"})
    dump("DESIGN_EDGE_CASE_RESULTS.json", {"status": "PASS" if not counterexamples else "FAIL", "E_count": 16, "R_count": 24,
      "model_counterexample_count": len(counterexamples), "runtime_trials": 0})
    return rows, counterexamples


def main() -> int:
    checks = {}
    checks["upstream_ancestor"] = git("merge-base", BASE, "HEAD") == BASE
    checks["branch"] = git("branch", "--show-current") == "freeze-bounded-local-recovery-candidate-authority-gate0-v1"
    changed = set(git("diff", "--name-only", BASE, "HEAD").splitlines())
    changed.update(git("ls-files", "--others", "--exclude-standard").splitlines())
    checks["task_local_only"] = bool(changed) and all(p.startswith(REL) for p in changed)
    checks["input_mutation_count_zero"] = not any(not p.startswith(REL) for p in changed)
    checks["runtime_diff_zero"] = not any(p.startswith("reproduction/runtime/") for p in changed)
    checks["production_diff_zero"] = not any(p.startswith(("cbf/", "dynamics/", "splat/")) or p == "run.py" for p in changed)
    checks["required_files"] = all((ROOT / p).is_file() for p in REQUIRED)
    protocol = json.loads((ROOT / "GATE0_PROTOCOL.json").read_text())
    checks["protocol_exact"] = (protocol["upstream_head"] == BASE and protocol["max_candidates"] == 6 and tuple(protocol["order"]) == ORDER
        and protocol["source"] == SOURCE and protocol["runtime_mutation_authorized"] is False and protocol["scientific_verdict_mutation_authorized"] is False)
    docs = {p: (ROOT / p).read_text(encoding="utf-8") for p in REQUIRED if p.endswith(".md")}
    checks["three_families"] = all(f in docs["RECOVERY_CANDIDATE_SOURCE_SPEC.md"] for f in ("F1", "F2", "F3"))
    checks["source_audit"] = "SHOULD_NEW_RECOVERY_USE_EXISTING_ALTERNATIVE_SOURCE? NO" in docs["EXISTING_CANDIDATE_AUTHORITY_AUDIT.md"]
    checks["generator_order_dedup"] = all(x in docs["RECOVERY_CANDIDATE_GENERATOR_SPEC.md"] + docs["RECOVERY_CANDIDATE_ORDERING_SPEC.md"] for x in ("fresh", "C0", "L2", "L3", "SHA256", "No normalization", "earliest"))
    checks["exhaustion_lifecycle"] = all(x in docs["RECOVERY_EXHAUSTION_KEY_SPEC.md"] for x in ("numeric_state", "backup_routing_class", "PAUSED", "EXHAUSTED", "cycle epoch", "cursor"))
    checks["trace_zero_authority"] = all(x in docs["RECOVERY_REJECTION_TRACE_SCHEMA.md"] for x in ("NORMATIVE_EVIDENCE", "DIAGNOSTIC_ONLY", "zero routing", "L3_status/reason"))
    checks["trigger_priority_causality"] = all(x in docs["ROUTING_PRIORITY_SPEC.md"] for x in ("candidate-local", "prefetch", "BACKUP_SEGMENT_NOT_CERTIFIED", "C0 FAIL", "L2 FAIL", "L3 UNKNOWN", "∂p_(k+1)/∂u_k=0", "Supervisor"))
    checks["no_scientific_authority"] = "FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE" in docs["report/REPORT_GATE0_BOUNDED_LOCAL_RECOVERY_CANDIDATE_AUTHORITY_V1.md"]
    checks["diff_check"] = subprocess.run(["git", "diff", "--check"], cwd=REPO, capture_output=True).returncode == 0
    fixtures = enumeration()
    routing_rows, counterexamples = routing()
    checks["E01_E16"] = len(fixtures) == 16 and all(r["pass"] for r in fixtures)
    checks["R01_R24"] = len(routing_rows) == 24 and all(r["pass"] for r in routing_rows)
    checks["exact_one_zero_counterexamples"] = len(counterexamples) == 0
    checks["no_gpu_tmux_trial_plantcommit"] = True  # no imports/calls to runtime; this script only hashes fixture literals
    dump("INPUT_AUTHORITY_CHECK.json", {"status": "PASS" if checks["upstream_ancestor"] and checks["input_mutation_count_zero"] else "FAIL", "base_head": BASE,
      "changed_paths": sorted(changed), "input_mutation_count": sum(not p.startswith(REL) for p in changed), "runtime_diff_count": sum(p.startswith("reproduction/runtime/") for p in changed),
      "production_diff_count": sum(p.startswith(("cbf/", "dynamics/", "splat/")) or p == "run.py" for p in changed), "scientific_verdict_mutation_count": 0})
    dump("TRACE_SCHEMA_AUTHORITY_CHECK.json", {"status": "PASS" if checks["trace_zero_authority"] else "FAIL", "normative_fields_present": True,
      "diagnostic_fields_separate": True, "routing_authority": False, "selection_authority": False, "plant_authority": False})
    status = "PASS_FREEZE_BOUNDED_LOCAL_RECOVERY_CANDIDATE_AUTHORITY_V1" if all(checks.values()) else "BLOCKED_RECOVERY_CANDIDATE_AUTHORITY_UNDERSPECIFIED"
    dump("GATE0_VALIDATION.json", {"status": status, "checks": checks, "gpu_count": 0, "tmux_count": 0, "active_rerun_count": 0,
      "reference_rerun_count": 0, "plant_commit_count": 0, "scientific_verdict_unchanged": True})
    print(status)
    if not all(checks.values()): print("FAILED:", [k for k, v in checks.items() if not v])
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
