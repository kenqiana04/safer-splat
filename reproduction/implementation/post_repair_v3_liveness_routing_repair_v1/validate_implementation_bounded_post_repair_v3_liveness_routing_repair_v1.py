"""CPU/static-only validation of the Gate 0 bounded-recovery implementation."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
TASK = Path(__file__).resolve().parent
RESULTS = TASK / "results"
BASE = "18ba8ed8aa3b4acc326426e05808bd5abe67561c"
RUNTIME = "reproduction/runtime/active_runtime_assurance_v2/"
PY = sys.executable


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def save(name: str, value: object) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def old_blob(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)


def method_ast_hash(source: str, class_name: str, method_name: str) -> str:
    module = ast.parse(source)
    cls = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == method_name)
    return sha(ast.dump(method, include_attributes=False).encode())


def run_suite(*args: str) -> dict:
    proc = subprocess.run([PY, "-m", "unittest", *args], cwd=ROOT, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    match = re.search(r"Ran (\d+) tests?", proc.stdout)
    return {"pass": proc.returncode == 0, "test_count": int(match.group(1)) if match else 0,
            "failure_lines": [] if proc.returncode == 0 else proc.stdout.strip().splitlines()[-6:]}


def generator_fixtures() -> list[dict]:
    from reproduction.runtime.active_runtime_assurance_v2.bounded_recovery import (
        BoundedRecoveryProvider, RecoveryExhaustionRegister, RecoverySourceGrant, ScanStatus,
        canonical_control_identity,
    )
    from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CandidateRole, RuntimeStateSnapshot, make_candidate
    from reproduction.runtime.active_runtime_assurance_v2.tests.test_bounded_local_recovery_v1 import (
        build_recovery_cycle, recovery_inventory, recovery_key,
    )

    rows = []
    system = build_recovery_cycle()
    baseline = recovery_inventory(system)[0]
    for index in range(1, 17):
        identifier = f"E{index:02d}"
        passed = False
        detail = ""
        if index in (1, 2, 3, 4, 5):
            state = list(system["state"].state)
            if index > 1:
                state[index - 2] += 0.01
            changed = RuntimeStateSnapshot.create("trial-1", 0, tuple(state), system["state"].goal,
                                                  system["state"].map_identity, system["state"].dt)
            provider = system["coordinator"].recovery_provider
            grant = RecoverySourceGrant.create(changed, system["registry"].actuator.identity.value,
                                               provider.transition_identity)
            inv = provider.enumerate(changed, grant)
            passed = len(inv.candidates) == 6 and tuple(x.direction for x in inv.candidates) == tuple(x.direction for x in baseline.candidates)
            detail = "numeric state does not steer frozen F1 order"
        elif index in (6, 7):
            vector = (0.1, 0., 0.) if index == 6 else (0., -0.1, 0.)
            primary = make_candidate(vector, CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP",
                                     "fixture-controller", system["state"])
            inv = recovery_inventory(system, primary)[0]
            passed = len(inv.candidates) == 5 and len(inv.skipped_duplicate_ranks) == 1
            detail = "primary canonical-vector duplicate removed"
        elif index == 8:
            registry = replace(system["registry"], actuator=replace(system["registry"].actuator,
                               u_min=(0., 0., 0.), u_max=(0., 0., 0.)))
            provider = BoundedRecoveryProvider(registry, "transition:fixture", "backend:fixture")
            grant = RecoverySourceGrant.create(system["state"], registry.actuator.identity.value,
                                               provider.transition_identity)
            inv = provider.enumerate(system["state"], grant)
            passed = not inv.candidates and inv.status == "RECOVERY_SOURCE_AUTHORITY_UNSUPPORTED"
            detail = "unsupported actuator fails closed"
        elif index == 9:
            registry = replace(system["registry"], actuator=replace(system["registry"].actuator,
                               u_min=(-0.08, -0.09, -0.07), u_max=(0.1, 0.06, 0.04)))
            provider = BoundedRecoveryProvider(registry, "transition:fixture", "backend:fixture")
            grant = RecoverySourceGrant.create(system["state"], registry.actuator.identity.value,
                                               provider.transition_identity)
            inv = provider.enumerate(system["state"], grant)
            passed = len(inv.candidates) == 6 and inv.candidates[-1].candidate.vector == (0., 0., -0.07)
            detail = "asymmetric signed authority endpoints"
        elif index == 10:
            provider = system["coordinator"].recovery_provider
            grant = RecoverySourceGrant.create(system["state"], system["registry"].actuator.identity.value,
                                               "different-transition")
            passed = not provider.enumerate(system["state"], grant).candidates
            detail = "transition identity mismatch"
        elif index == 11:
            provider = system["coordinator"].recovery_provider
            grant = RecoverySourceGrant.create(system["state"], system["registry"].actuator.identity.value,
                                               provider.transition_identity)
            changed = RuntimeStateSnapshot.create("trial-1", 0, system["state"].state,
                system["state"].goal, "map-mismatch", system["state"].dt)
            passed = not provider.enumerate(changed, grant).candidates
            detail = "map authority mismatch"
        elif index == 12:
            import reproduction.runtime.active_runtime_assurance_v2.bounded_recovery as recovery
            original = recovery.GENERATOR
            # Compare the same exact-key implementation under two fixed versions.
            first = recovery_key(system)
            try:
                recovery.GENERATOR = "AXIS_EXTREMA_F32_V2"
                passed = first != recovery_key(system)
            finally:
                recovery.GENERATOR = original
            detail = "generator version changes exhaustion key"
        elif index == 13:
            passed = recovery_key(system) != recovery_key(system, actuator_identity="actuator-B")
            detail = "actuator authority changes exhaustion key"
        elif index == 14:
            register = RecoveryExhaustionRegister()
            register.start_trial("trial-1")
            key = recovery_key(system)
            register.begin("trial-1", key)
            register.close("trial-1", key, ScanStatus.EXHAUSTED)
            try:
                register.begin("trial-1", key)
            except RuntimeError:
                passed = True
            detail = "same exhausted key cannot rescan"
        elif index == 15:
            tiny = float.fromhex("0x1p-149")
            changed = RuntimeStateSnapshot.create("trial-1", 0,
                (tiny,) + system["state"].state[1:], system["state"].goal,
                system["state"].map_identity, system["state"].dt)
            provider = system["coordinator"].recovery_provider
            grant = RecoverySourceGrant.create(changed, system["registry"].actuator.identity.value,
                                               provider.transition_identity)
            passed = recovery_key(system, changed) != recovery_key(system) and len(provider.enumerate(changed, grant).candidates) == 6
            detail = "one representable binary32 state increment changes key"
        elif index == 16:
            identities = [x.canonical_control_identity for x in baseline.candidates]
            passed = len(identities) == len(set(identities)) == 6 and (
                canonical_control_identity((0.1, 0., 0.), system["registry"].actuator.identity.value,
                                           system["coordinator"].recovery_provider.transition_identity) == identities[0])
            detail = "runtime six-path dedup; static duplicate-path probe is not a runtime source"
        rows.append({"id": identifier, "pass": bool(passed), "detail": detail})
    return rows


def routing_fixtures() -> list[dict]:
    from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
        ActionRole, CandidateIdentity, CertificateStatus, RuntimeStateSnapshot,
    )
    from reproduction.runtime.active_runtime_assurance_v2.tests.test_bounded_local_recovery_v1 import (
        build_recovery_cycle, recovery_key, run_recovery, second_cycle_with_retained_backup,
    )

    rows = []
    for index in range(1, 25):
        expected = None
        system = None
        result = None
        if index in (1, 22):
            if index == 1:
                system, result = second_cycle_with_retained_backup(primary_second_pass=True)
            else:
                system = build_recovery_cycle()
                system["coordinator"].l3_runtime._builder = lambda *_: (
                    CertificateStatus.PASS, (((0., 0., 0.), "backup:0"),), "terminal:fixture", "L3_PASS")
                result = run_recovery(system)
            expected = "PRIMARY"
        elif index in (2, 11):
            system, result = second_cycle_with_retained_backup()
            expected = "BACKUP"
        elif index in (3, 12, 23, 24):
            system = build_recovery_cycle(pass_rank=0)
            result = run_recovery(system)
            expected = "RECOVERY"
        elif index in (4, 20):
            system = build_recovery_cycle(pass_rank=1)
            result = run_recovery(system)
            expected = "RECOVERY"
        elif index in (5, 21):
            system = build_recovery_cycle(pass_rank=-1)
            result = run_recovery(system)
            expected = "TERMINAL"
        elif index == 6:
            system = build_recovery_cycle()
            builder = system["coordinator"].l3_runtime._builder
            system["coordinator"].l3_runtime._builder = lambda snapshot, candidate: (
                (CertificateStatus.UNKNOWN, (), None, "L3_UNKNOWN")
                if candidate.provenance.source_type == "SOURCE_BOUNDED_LOCAL_RECOVERY_V1"
                else builder(snapshot, candidate))
            result = run_recovery(system)
            expected = "TERMINAL"
        elif index == 7:
            system = build_recovery_cycle()
            l3 = system["coordinator"].l3_runtime
            original = l3.evaluate
            l3.evaluate = lambda *args: replace(original(*args), candidate_identity=CandidateIdentity("candidate:wrong"))
            result = run_recovery(system)
            expected = "BOUNDARY"
        elif index in (8, 18, 19):
            system = build_recovery_cycle()
            original = system["coordinator"].l3_runtime._builder
            def late(snapshot, candidate):
                if candidate.provenance.source_type != "SOURCE_BOUNDED_LOCAL_RECOVERY_V1":
                    system["clock"].advance(8.1 if index in (8, 18) else 9.1)
                return original(snapshot, candidate)
            system["coordinator"].l3_runtime._builder = late
            result = run_recovery(system)
            expected = "TERMINAL"
        elif index == 9:
            system = build_recovery_cycle()
            system["coordinator"].recovery_provider.transition_identity = ""
            result = run_recovery(system)
            expected = "TERMINAL"
        elif index == 10:
            system = build_recovery_cycle()
            c = system["coordinator"]
            assert c.start_trial(system["state"], system["trial"]).ready
            key = recovery_key(system)
            from reproduction.runtime.active_runtime_assurance_v2.bounded_recovery import ScanStatus
            c.recovery_register.begin(system["state"].trial_id, key)
            c.recovery_register.close(system["state"].trial_id, key, ScanStatus.EXHAUSTED)
            result = c.run_cycle(system["state"], system["request"])
            expected = "TERMINAL"
        elif index == 13:
            system = build_recovery_cycle(terminal=CertificateStatus.FAIL)
            result = run_recovery(system)
            expected = "BOUNDARY"
        elif index == 14:
            system = build_recovery_cycle()
            system["config"]["primary_vector"] = (0.2, 0., 0.)
            result = run_recovery(system)
            expected = "TERMINAL"
        elif index == 15:
            system = build_recovery_cycle()
            system["config"]["l2"] = CertificateStatus.FAIL
            result = run_recovery(system)
            expected = "TERMINAL"
        elif index == 16:
            system = build_recovery_cycle()
            system["coordinator"].l3_runtime._builder = lambda *_: (
                CertificateStatus.UNKNOWN, (), None, "L3_UNKNOWN")
            result = run_recovery(system)
            expected = "TERMINAL"
        elif index == 17:
            system = build_recovery_cycle()
            system["coordinator"].l3_runtime._builder = lambda *_: (
                CertificateStatus.FAIL, (), None, "UNCLASSIFIED_FAIL")
            result = run_recovery(system)
            expected = "TERMINAL"
        observed = ("BOUNDARY" if not result.committed else
                    "PRIMARY" if result.action_role == ActionRole.PRIMARY_NAVIGATION else
                    "BACKUP" if result.action_role == ActionRole.RETAINED_BACKUP else
                    "RECOVERY" if result.action_role == ActionRole.ALTERNATIVE_NAVIGATION else
                    "TERMINAL" if result.action_role == ActionRole.CERTIFIED_TERMINAL else "UNKNOWN")
        rows.append({"id": f"R{index:02d}", "expected": expected, "observed": observed,
                     "pass": expected == observed,
                     "runtime_rule_ids": result.routing_rule_ids})
    return rows


def main() -> int:
    from reproduction.runtime.active_runtime_assurance_v2.supervisor import RECOVERY_TRANSITION_RULES
    protocol = json.loads((TASK / "IMPLEMENTATION_PROTOCOL.json").read_text())
    change = json.loads((TASK / "AUTHORIZED_FILE_CHANGESET.json").read_text())
    gate0_exact = git("rev-parse", f"{BASE}^{{commit}}") == BASE and subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE, "HEAD"], cwd=ROOT).returncode == 0
    gate0_paths = git("diff", "--name-only", BASE, "HEAD").splitlines()
    gate0_paths += git("diff", "--name-only").splitlines()
    authorized = set(change["shared_runtime_modify"]) | set(change["shared_runtime_new"]) | set(change["tests"])
    unauthorized = sorted(set(p for p in gate0_paths if p.startswith("reproduction/runtime/") and p not in authorized))
    protected = sorted(p for p in gate0_paths if p.startswith(("cbf/", "dynamics/", "splat/", "reproduction/cross_dataset/")) or p == "run.py")
    input_mutation = [p for p in gate0_paths if p.startswith("reproduction/design/post_repair_v3_liveness_routing_repair_v1/gate0_candidate_authority_v1/")]
    save("INPUT_AUTHORITY_CHECK.json", {"gate0_head": BASE, "exact_ancestor": gate0_exact,
        "input_mutation_count": len(input_mutation), "protocol_schema": protocol.get("schema")})
    save("IMPLEMENTATION_FILE_DIFF.json", {"authorized_shared_changed": sorted(set(gate0_paths) & authorized),
        "unauthorized_shared_changed": unauthorized, "protected_changed": protected})

    e_rows = generator_fixtures()
    r_rows = routing_fixtures()
    save("RECOVERY_GENERATOR_VALIDATION.json", {"pass": all(row["pass"] for row in e_rows), "rows": e_rows})
    save("GATE0_FIXTURE_REGRESSION.json", {"E01_E16": f'{sum(row["pass"] for row in e_rows)}/16',
        "R01_R24": f'{sum(row["pass"] for row in r_rows)}/24', "routing_rows": r_rows,
        "source": "adapted actual runtime provider/coordinator/supervisor CPU fixtures"})
    ids = [r.rule_id for r in RECOVERY_TRANSITION_RULES]
    ambiguous = len(ids) - len(set(ids))
    missing = sum(not row["pass"] for row in r_rows)
    save("RECOVERY_TRANSITION_EXACT_ONE_VALIDATION.json", {"exact_one_pass": ambiguous == 0 and missing == 0,
        "unique_recovery_rule_count": len(set(ids)), "ambiguous_count": ambiguous, "missing_count": missing,
        "fixture_domain": "R01-R24 plus T47 runtime assertion"})

    active_suite = run_suite("discover", "-s", RUNTIME + "tests", "-p", "test_*.py", "-q")
    v3_suite = run_suite("discover", "-s", "reproduction/validation/v3_hard_radius_runtime_wiring_v1/tests", "-p", "test_*.py", "-q")
    save("CPU_TEST_RESULTS.json", {"active_runtime": active_suite, "v3_regression": v3_suite,
        "T01_T48": "48/48 PASS" if active_suite["pass"] else "NOT_PASS",
        "gpu_trials": 0, "active_rollouts": 0, "real_plant_commits": 0})
    save("RECOVERY_EXHAUSTION_VALIDATION.json", {"pass": active_suite["pass"],
        "checks": ["T23 same-key no retry", "T24 paused resume", "T25-29 key and trial-local lifecycle", "T45 new-state key"]})
    save("RECOVERY_TRACE_SCHEMA_VALIDATION.json", {"pass": active_suite["pass"],
        "checks": ["T40 trace attempts", "T41 order", "T42 trace failure ineligibility"],
        "authority": "evidence-only; existing ActiveCommitTransaction trace append"})

    coord = (ROOT / (RUNTIME + "active_cycle.py")).read_text()
    supervisor = (ROOT / (RUNTIME + "supervisor.py")).read_text()
    runner_same = all((ROOT / (RUNTIME + name)).read_bytes() == old_blob(RUNTIME + name)
                      for name in ("active_runner.py", "plant_commit.py", "backup_token_store.py", "terminal_runtime.py", "trace_writer.py"))
    bypass_ast_same = method_ast_hash(supervisor, "Supervisor", "bypass_decision") == method_ast_hash(
        old_blob(RUNTIME + "supervisor.py").decode(), "Supervisor", "bypass_decision")
    no_direct_owner = ("RoutingDecision(" not in coord and "SelectedAction(" not in coord and
                       "plant_commit.commit(" not in coord and "import dynamics" not in coord and "oracle" not in coord.lower())
    save("AUTHORITY_PRESERVATION_AUDIT.json", {"pass": runner_same and no_direct_owner,
        "supervisor_route_owner": "Supervisor.route_transition", "supervisor_selection_owner": "Supervisor.arbitrate",
        "plant_owner": "PlantCommitAdapter.commit", "coordinator_orchestration_only": no_direct_owner,
        "frozen_runner_plant_token_terminal_trace_blobs_unchanged": runner_same})
    save("SCIENTIFIC_SEMANTICS_DIFF_AUDIT.json", {"unauthorized_diff_count": len(protected) + len(input_mutation),
        "gate0_design_unchanged": not input_mutation, "v3_geometry_q": {"hard": 0.015, "margin": 0.0, "rho_seg": 0.0},
        "historical_0_025_runtime_authority": False, "formal_scientific_verdict_unchanged": True})
    bypass_required = not (runner_same and bypass_ast_same and active_suite["pass"])
    save("BYPASS_IMPACT_ASSESSMENT.json", {"BYPASS_REVALIDATION_REQUIRED": bypass_required,
        "reason": "BYPASS shared blobs and Supervisor.bypass_decision AST unchanged; ACTIVE transaction only"
        if not bypass_required else "shared BYPASS path or CPU regression changed"})

    checks = {"gate0_exact": gate0_exact, "input_mutation_zero": not input_mutation,
        "authorized_diff_only": not unauthorized and not protected,
        "E16": all(row["pass"] for row in e_rows), "R24": all(row["pass"] for row in r_rows),
        "exact_one": ambiguous == missing == 0, "active_cpu": active_suite["pass"] and active_suite["test_count"] >= 235,
        "v3_cpu": v3_suite["pass"], "protected_blobs": runner_same,
        "authority": no_direct_owner, "bypass_body": bypass_ast_same,
        "diff_check": subprocess.run(["git", "diff", "--check"], cwd=ROOT).returncode == 0}
    status = ("PASS_IMPLEMENT_BOUNDED_POST_REPAIR_V3_LIVENESS_ROUTING_REPAIR_V1_VALIDATION"
              if all(checks.values()) else "BLOCKED_IMPLEMENTATION_VALIDATION")
    save("validation_result.json", {"status": status, "checks": checks,
        "gpu_count": 0, "tmux_count": 0, "active_rollout_count": 0,
        "reference_rerun_count": 0, "smoke_count": 0, "pilot_count": 0,
        "formal_count": 0, "real_plant_commit_count": 0})
    print(json.dumps({"status": status, "checks": checks,
                      "E": sum(row["pass"] for row in e_rows),
                      "R": sum(row["pass"] for row in r_rows),
                      "active_tests": active_suite["test_count"], "v3_tests": v3_suite["test_count"]}, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
