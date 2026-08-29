"""Read-only line tracer for exact frozen run.py controller facts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from canonical_trace_hash import semantic_sha256


def _vector(value: Any) -> list[float] | None:
    if value is None:
        return None
    snapshot = value.detach() if hasattr(value, "detach") else value
    if hasattr(snapshot, "cpu"):
        snapshot = snapshot.cpu()
    if hasattr(snapshot, "contiguous"):
        snapshot = snapshot.contiguous()
    if hasattr(snapshot, "numpy"):
        snapshot = snapshot.numpy()
    if hasattr(snapshot, "tolist"):
        snapshot = snapshot.tolist()
    return [float(item) for item in snapshot]


class FrozenRunTraceCapture:
    """Capture facts without replacing controller, CBF, or plant callables."""

    def __init__(self, run_path: Path, *, trial_id: int, seed: int, map_authority_id: str) -> None:
        self.run_path = str(Path(run_path).resolve())
        self.trial_id = int(trial_id)
        self.seed = int(seed)
        self.map_authority_id = str(map_authority_id)
        self.steps: list[dict[str, Any]] = []
        self.current: dict[str, Any] | None = None
        self.line_events = 0

    def _finish_current(self) -> None:
        if self.current is None:
            return
        current = self.current
        if current.get("solver_success") is True and current.get("plant_output_x_next") is not None:
            if current["controller_branch"] == "SOLVER_SUCCESS":
                current["controller_branch"] = "SOLVER_SUCCESS_PLANT"
        for key in ("x_k", "u_des", "selected_u_k"):
            current[f"{key}_semantic_hash"] = None if current.get(key) is None else semantic_sha256(current[key])
        current["selected_candidate_identity"] = (
            None if current.get("selected_u_k") is None else "FROZEN_SOLVE_QP_RETURN"
        )
        current["selected_candidate_hash"] = current.get("selected_u_k_semantic_hash")
        current["step_semantic_hash"] = semantic_sha256({
            key: value for key, value in current.items() if key != "step_semantic_hash"
        })
        self.steps.append(current)
        self.current = None

    def __call__(self, frame, event: str, arg):
        if str(Path(frame.f_code.co_filename).resolve()) != self.run_path:
            return None
        if event == "line":
            self.line_events += 1
            line = frame.f_lineno
            local = frame.f_locals
            if line == 132:
                self._finish_current()
                self.current = {
                    "trial_id": self.trial_id,
                    "step_id": int(local["i"]),
                    "seed": self.seed,
                    "x_k": _vector(local.get("x")),
                    "u_des": _vector(local.get("u_des")),
                    "selected_u_k": None,
                    "solver_success": None,
                    "controller_branch": "PRE_SOLVE",
                    "plant_input_x": None,
                    "plant_input_u": None,
                    "plant_output_x_next": None,
                    "termination_flag": False,
                    "termination_reason": "CONTINUE",
                    "goal": _vector(local.get("goal")),
                    "goal_terminal_status": "NOT_TERMINAL",
                    "map_authority_id": self.map_authority_id,
                }
            elif line == 136 and self.current is not None:
                self.current["selected_u_k"] = _vector(local.get("u"))
                self.current["solver_success"] = bool(getattr(local.get("cbf"), "solver_success", False))
                self.current["controller_branch"] = "SOLVER_SUCCESS" if self.current["solver_success"] else "SOLVER_FAILURE"
            elif line == 140 and self.current is not None:
                self.current.update({
                    "termination_flag": True,
                    "termination_reason": "SOLVER_FAILED",
                    "goal_terminal_status": "NOT_REACHED",
                    "controller_branch": "SOLVER_FAILURE_STOP",
                })
            elif line == 147 and self.current is not None:
                self.current["plant_input_x"] = _vector(local.get("x"))
                self.current["plant_input_u"] = _vector(local.get("u"))
            elif line == 149 and self.current is not None:
                self.current["plant_output_x_next"] = _vector(local.get("x"))
            elif line == 168 and self.current is not None:
                self.current.update({
                    "termination_flag": True,
                    "termination_reason": "REACHED_GOAL",
                    "goal_terminal_status": "REACHED_GOAL",
                    "controller_branch": "SOLVER_SUCCESS_PLANT_REACHED_GOAL",
                })
            elif line == 171 and self.current is not None:
                self.current.update({
                    "termination_flag": True,
                    "termination_reason": "STALLED_BEFORE_GOAL",
                    "goal_terminal_status": "NOT_REACHED",
                    "controller_branch": "SOLVER_SUCCESS_PLANT_STALLED",
                })
            elif line == 177 and self.current is not None:
                self.current.update({
                    "termination_flag": True,
                    "termination_reason": "MAX_STEPS_LOOSE_SUCCESS",
                    "goal_terminal_status": "MAX_STEPS",
                    "controller_branch": "SOLVER_SUCCESS_PLANT_MAX_STEPS",
                })
            elif line == 180:
                self._finish_current()
        elif event == "return":
            self._finish_current()
        return self

    def to_record(self, *, run_id: str, arm: str) -> dict[str, Any]:
        self._finish_current()
        result = {
            "schema_version": "L2_H1_SHADOW_EQUIVALENCE_PRIMARY_TRACE_V1",
            "run_id": str(run_id),
            "arm": str(arm),
            "trial_id": self.trial_id,
            "seed": self.seed,
            "map_authority_id": self.map_authority_id,
            "qa_only": True,
            "line_trace_event_count": self.line_events,
            "steps": self.steps,
        }
        result["primary_trace_semantic_hash"] = semantic_sha256({
            "trial_id": result["trial_id"],
            "seed": result["seed"],
            "map_authority_id": result["map_authority_id"],
            "steps": result["steps"],
        })
        return result
