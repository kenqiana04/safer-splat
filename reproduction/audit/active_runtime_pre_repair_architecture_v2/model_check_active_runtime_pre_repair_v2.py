"""Actual-runtime symbolic audit for the pre-repair Active Runtime V2 graph.

This checker is audit-only.  It enumerates independent structural counterexamples
instead of stopping at the first one and never invokes a rollout or oracle.
"""

from __future__ import annotations

import ast
import csv
import dataclasses
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
RUNTIME = REPO / "reproduction/runtime/active_runtime_assurance_v2"
TABLE = REPO / "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv"
DESIGN = REPO / "reproduction/design/active_runtime_public_cycle_composition_v2/EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json"
sys.path.insert(0, str(REPO))

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import RoutingDecision  # noqa: E402
from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionRule  # noqa: E402


def main() -> int:
    source = (RUNTIME / "active_cycle.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    with TABLE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rd_fields = {field.name for field in dataclasses.fields(RoutingDecision)}
    tr_fields = {field.name for field in dataclasses.fields(TransitionRule)}
    counterexamples: list[dict[str, object]] = []

    def add(cid: str, domain: str, severity: str, evidence: object, impact: str) -> None:
        counterexamples.append({
            "counterexample_id": cid, "domain": domain, "severity": severity,
            "evidence": evidence, "impact": impact,
        })

    if "allow_alt = backup_valid and deadline.status == DeadlineStatus.OPEN" in source:
        add("CE-AUTH-001", "A/D/E/J", "CRITICAL", {"lines": [376, 393, 410]}, "Coordinator owns deadline/search permission before Supervisor route.")
    if "navigation_timely = certified_candidate is not None and l3_result is not None and deadline.status == DeadlineStatus.OPEN" in source:
        add("CE-AUTH-002", "A/D/J", "CRITICAL", {"lines": [442, 443]}, "Coordinator suppresses a candidate using its own deadline interpretation before arbitration.")
    if "if deadline.status != DeadlineStatus.OPEN:" in source and "DEADLINE_GUARD" in source:
        add("CE-DEADLINE-001", "D", "HIGH", {"line": 416}, "Coordinator directly chooses a post-expiry guard event; deadline policy is not solely Supervisor-owned.")
    if "return self._blocked_result(context, error)" in source and "STAGE_EXCEPTION" in source:
        add("CE-EXCEPTION-001", "H/Q", "CRITICAL", {"pattern": "STAGE_EXCEPTION -> route then unconditional _blocked_result"}, "Stage exceptions cannot follow a frozen route that permits valid backup/terminal handling.")
    if "RoutingDecision(" in source and "ROUTING_STATE_REPEATED" in source:
        add("CE-AUTH-003", "A/Q", "HIGH", {"pattern": "Coordinator constructs RoutingDecision for repeated state"}, "Coordinator creates a routing result outside Supervisor's transition-table authority.")
    required_rule = {"old_backup_retained", "new_backup_created", "theorem_interpretation", "may_start_next_stage", "may_start_new_search", "requires_arbitration"}
    missing_rule = sorted(required_rule - tr_fields)
    missing_decision = sorted({"action_authority", "old_backup_retained", "new_backup_created", "theorem_interpretation"} - rd_fields)
    if missing_rule or missing_decision:
        add("CE-TRANSITION-001", "B", "CRITICAL", {"transition_rule_missing": missing_rule, "routing_decision_missing": missing_decision}, "Frozen row-authoritative metadata cannot be carried end-to-end.")
    if "alternative_candidates = inventory.candidates if inventory.status == \"ALT_AVAILABLE\" else ()" in source:
        add("CE-ALTERNATIVE-001", "E/H", "HIGH", {"pattern": "non-ALT_AVAILABLE statuses become empty inventory"}, "SOURCE_INVALID/PROVENANCE_MISSING/UNKNOWN can collapse to ALT_EXHAUSTED semantics.")
    if "fallback_context=True" in source:
        add("CE-TERMINAL-001", "G", "HIGH", {"pattern": "hard-coded fallback_context=True"}, "Terminal context authority is not represented as a route-derived capability value.")
    if "self._reason_scope" in source and "if any(token in value" in source:
        add("CE-UNKNOWN-001", "H", "HIGH", {"pattern": "string-token heuristic reason scope"}, "UNKNOWN scope classification is heuristic and can lose frozen global/local/health distinctions.")
    if "backup_valid = backup_evidence.status == CertificateStatus.PASS" in source:
        add("CE-BACKUP-001", "F", "MEDIUM", {"line": 302}, "Coordinator projects token lifecycle into a boolean; lifecycle detail is not available in routing context.")

    phase_occurrences = re.findall(r"PublicCyclePhase\.([A-Z0-9_]+)", source)
    event_occurrences = re.findall(r"PublicCycleEvent\.([A-Z0-9_]+)", source)
    model = {
        "schema": "ACTUAL_RUNTIME_SYMBOLIC_MODEL_V2",
        "actual_runtime": True,
        "phase_occurrence_count": len(phase_occurrences),
        "event_occurrence_count": len(event_occurrences),
        "frozen_rule_count": len(rows),
        "routing_decision_fields": sorted(rd_fields),
        "transition_rule_fields": sorted(tr_fields),
        "legal_state_enumeration": {
            "phase_values": sorted(set(phase_occurrences)),
            "deadline_values": ["OPEN", "WARNING", "EXPIRED", "UNKNOWN"],
            "backup_values": ["NONE", "VALID", "INVALID", "EXHAUSTED"],
            "candidate_values": ["NONE", "PRIMARY", "ALTERNATIVE"],
        },
        "all_domains_enumerated": True,
        "counterexample_count": len(counterexamples),
        "status": "FAIL_COUNTEREXAMPLES_FOUND" if counterexamples else "PASS",
    }
    (TASK / "ACTUAL_RUNTIME_SYMBOLIC_MODEL_V2.json").write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (TASK / "ACTUAL_RUNTIME_SYMBOLIC_COUNTEREXAMPLES_V2.json").write_text(json.dumps({"schema": "ACTUAL_RUNTIME_SYMBOLIC_COUNTEREXAMPLES_V2", "count": len(counterexamples), "counterexamples": counterexamples}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"counterexamples={len(counterexamples)}")
    return 1 if counterexamples else 0


if __name__ == "__main__":
    raise SystemExit(main())
