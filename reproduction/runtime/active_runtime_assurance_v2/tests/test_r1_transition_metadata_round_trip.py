import csv
import json
import unittest
from pathlib import Path

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    CandidateIdentity,
    CandidateRole,
    DeadlineObservation,
    DeadlineStatus,
    PublicCycleEvent,
    RuntimePhase,
    RuntimeRoutingContext,
)
from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionTable


ROOT = Path(__file__).resolve().parents[3]
TABLE = ROOT / "specification" / "method_logic_closure_v2" / "STATE_TRANSITION_TABLE_V2.csv"


class R1TransitionMetadataRoundTripTests(unittest.TestCase):
    def _context_for(self, row: dict[str, str], authority: str) -> RuntimeRoutingContext:
        requirement = row["deadline_requirement"]
        status = DeadlineStatus.WARNING if requirement == "GUARD_OR_EXPIRED" else DeadlineStatus.OPEN
        candidate_requirement = row["candidate_requirement"]
        candidate_role = None
        candidate_available = candidate_requirement != "NONE"
        if candidate_requirement in {"PRIMARY", "PRIMARY_OR_ALTERNATIVE"}:
            candidate_role = CandidateRole.PRIMARY
        elif candidate_requirement == "ALTERNATIVE":
            candidate_role = CandidateRole.ALTERNATIVE
        backup_requirement = row["retained_backup_requirement"]
        backup_present = backup_requirement == "VALID"
        backup_valid = backup_requirement == "VALID"
        terminal_evaluated = row["rule_id"] in {"ARB_TERMINAL", "ARB_BOUNDARY"}
        terminal_eligible = row["rule_id"] == "ARB_TERMINAL"
        certified = row["rule_id"] == "ARB_NAV"
        return RuntimeRoutingContext(
            source_phase=RuntimePhase(row["source_phase"]),
            deadline=DeadlineObservation(status, row["source_phase"], 0.0, 1.0, "deadline:r1"),
            authority_identity=authority,
            candidate_role=candidate_role,
            candidate_identity=CandidateIdentity("candidate:r1") if candidate_available else None,
            candidate_available=candidate_available,
            retained_backup_present=backup_present,
            retained_backup_valid=backup_valid,
            terminal_evaluated=terminal_evaluated,
            certified_candidate_available=certified,
            terminal_evidence_eligible=terminal_eligible,
        )

    def test_all_frozen_rows_round_trip_into_routing_decision(self):
        table = TransitionTable.from_csv(TABLE)
        design = json.loads((ROOT / "design" / "active_runtime_public_cycle_composition_v2" / "EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json").read_text(encoding="utf-8"))
        design_by_id = {item["rule_id"]: item for item in design["rules"]}
        self.assertEqual(len(table.rules), 43)
        with TABLE.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            rule = table.by_id[row["rule_id"]]
            context = self._context_for(row, "transition:r1")
            decision = table.resolve(PublicCycleEvent(row["observation/result"]), context)
            self.assertEqual(decision.rule_id, rule.rule_id, row["rule_id"])
            for field in (
                "source_phase", "destination_phase", "commit_allowed", "action_authority",
                "failure_code", "observation_result", "reason_scope", "retained_backup_requirement",
                "deadline_requirement", "candidate_requirement", "guard", "may_start_next_stage",
                "may_start_new_search", "requires_arbitration", "deadline_interpretation",
                "backup_routing_allowed", "terminal_routing_allowed", "old_backup_retained",
                "new_backup_created", "theorem_interpretation",
            ):
                expected = getattr(rule, field)
                if field == "source_phase":
                    self.assertEqual(decision.source_phase.value, expected, row["rule_id"])
                elif field == "destination_phase":
                    self.assertEqual(decision.destination_phase.value, expected, row["rule_id"])
                elif field == "failure_code":
                    self.assertEqual(decision.failure_mapping, expected or None, row["rule_id"])
                elif field == "guard":
                    self.assertEqual(decision.guard, expected, row["rule_id"])
                elif hasattr(decision, field):
                    self.assertEqual(getattr(decision, field), expected, f"{row['rule_id']}:{field}")
            self.assertEqual(rule.theorem_interpretation, design_by_id[row["rule_id"]]["theorem_interpretation"])


if __name__ == "__main__":
    unittest.main()
