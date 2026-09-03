"""Sole plant/dynamics commit authority for the additive active package."""

from __future__ import annotations

import importlib
from typing import Callable

from .authority_registry import AuthorityRegistry
from .runtime_errors import CommitAuthorityViolation
from .runtime_types import ActionRole, CommitReceipt, RuntimeStateSnapshot, SelectedAction, SupervisorDecision, all_finite


LEGAL_ROLES = {ActionRole.PRIMARY_NAVIGATION, ActionRole.ALTERNATIVE_NAVIGATION, ActionRole.RETAINED_BACKUP, ActionRole.CERTIFIED_TERMINAL}


def _reference_transition(state: tuple[float, ...], control: tuple[float, ...], dt: float) -> tuple[float, ...]:
    torch = importlib.import_module("torch")
    double_integrator_dynamics = importlib.import_module("dynamics.systems").double_integrator_dynamics
    x = torch.tensor(state, dtype=torch.float32)
    u = torch.tensor(control, dtype=torch.float32)
    return tuple(float(value) for value in (x + double_integrator_dynamics(x, u) * float(dt)).tolist())


class PlantCommitAdapter:
    def __init__(self, registry: AuthorityRegistry, transition: Callable[[tuple[float, ...], tuple[float, ...], float], tuple[float, ...]] | None = None) -> None:
        self._registry = registry
        self._transition = transition or _reference_transition
        self.commit_count = 0

    def commit(self, decision: SupervisorDecision, snapshot: RuntimeStateSnapshot, selected_action: SelectedAction) -> CommitReceipt:
        if not decision.allows_commit or decision.selected_action is None or selected_action.role not in LEGAL_ROLES:
            raise CommitAuthorityViolation("SUPERVISOR_COMMIT_AUTHORITY_REQUIRED")
        if decision.cycle_index != snapshot.cycle_index or decision.state_identity != snapshot.identity:
            raise CommitAuthorityViolation("STATE_OR_CYCLE_IDENTITY_MISMATCH")
        if decision.selected_action.identity != selected_action.identity or decision.selected_action.vector != selected_action.vector or decision.selected_action.role != selected_action.role:
            raise CommitAuthorityViolation("SELECTED_ACTION_IDENTITY_MISMATCH")
        # BYPASS has no active authority: it delegates the exact reference action,
        # including the reference path's native numerical behavior.  ACTIVE rules
        # retain the frozen actuator-admission guard without clipping or tolerance.
        if decision.rule_id != "BYPASS" and (not all_finite(selected_action.vector) or any(value < low or value > high for value, low, high in zip(selected_action.vector, self._registry.actuator.u_min, self._registry.actuator.u_max))):
            raise CommitAuthorityViolation("ACTUATOR_ADMISSION_REQUIRED")
        try:
            post_vector = self._transition(snapshot.state, selected_action.vector, snapshot.dt)
            post = RuntimeStateSnapshot.create(snapshot.trial_id, snapshot.cycle_index + 1, post_vector, snapshot.goal, snapshot.map_identity, snapshot.dt)
        except Exception as exc:
            return CommitReceipt(snapshot.cycle_index, snapshot.identity, selected_action.identity, selected_action.identity, selected_action.vector, selected_action.role, None, None, False, f"PLANT_COMMIT_EXCEPTION:{type(exc).__name__}")
        self.commit_count += 1
        return CommitReceipt(snapshot.cycle_index, snapshot.identity, selected_action.identity, selected_action.identity, selected_action.vector, selected_action.role, post, post.identity, True, "COMMITTED")
