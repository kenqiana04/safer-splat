#!/usr/bin/env python3
"""Bounded warning-streak slowdown policy with no simulation dependencies."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


CLAIM_SCOPE = "minimal_active_policy_smoke"


@dataclass(frozen=True)
class SlowdownPolicyConfig:
    enabled: bool = True
    min_scale: float = 0.25
    warning_scale: float = 0.75
    persistent_warning_scale: float = 0.5
    critical_warning_scale: float = 0.25
    enter_warning_streak: int = 1
    persistent_warning_streak: int = 2
    critical_warning_streak: int = 3
    clear_streak_to_release: int = 2
    max_delta_scale_per_step: float = 0.25


@dataclass(frozen=True)
class SlowdownPolicyInput:
    step: int
    warning_streak: int
    clear_streak: int
    dt_warning_any: bool
    h1_warning: bool
    h2_warning: bool
    h3_warning: bool
    qp_infeasible: bool
    recovery_used: bool
    collision: bool
    previous_scale: float


@dataclass(frozen=True)
class SlowdownPolicyDecision:
    active: bool
    scale: float
    reason_code: str
    claim_scope: str
    modifies_control: bool
    bounded: bool
    notes: str


def _validate_config(config: SlowdownPolicyConfig) -> None:
    scales = (
        config.min_scale,
        config.warning_scale,
        config.persistent_warning_scale,
        config.critical_warning_scale,
        config.max_delta_scale_per_step,
    )
    if not all(math.isfinite(value) for value in scales):
        raise ValueError("all scale parameters must be finite")
    if not 0.0 < config.min_scale <= 1.0:
        raise ValueError("min_scale must be in (0, 1]")
    if not (
        config.min_scale
        <= config.critical_warning_scale
        <= config.persistent_warning_scale
        <= config.warning_scale
        <= 1.0
    ):
        raise ValueError("slowdown scales must be monotone and within [min_scale, 1]")
    if not 0.0 < config.max_delta_scale_per_step <= 1.0:
        raise ValueError("max_delta_scale_per_step must be in (0, 1]")
    if not (
        1
        <= config.enter_warning_streak
        <= config.persistent_warning_streak
        <= config.critical_warning_streak
    ):
        raise ValueError("warning streak thresholds must be positive and monotone")
    if config.clear_streak_to_release < 1:
        raise ValueError("clear_streak_to_release must be positive")


def _normal_previous_scale(
    previous_scale: float, config: SlowdownPolicyConfig
) -> tuple[float, bool]:
    if not math.isfinite(previous_scale):
        return 1.0, False
    if previous_scale < config.min_scale or previous_scale > 1.0:
        return min(1.0, max(config.min_scale, previous_scale)), False
    return previous_scale, True


def _ramp_toward(current: float, target: float, max_delta: float) -> float:
    delta = target - current
    if abs(delta) <= max_delta:
        return target
    return current + math.copysign(max_delta, delta)


def compute_warning_slowdown(
    policy_input: SlowdownPolicyInput,
    config: SlowdownPolicyConfig,
) -> SlowdownPolicyDecision:
    """Compute one bounded policy decision without touching a control vector."""

    _validate_config(config)
    previous, previous_valid = _normal_previous_scale(
        policy_input.previous_scale, config
    )

    if not config.enabled:
        return SlowdownPolicyDecision(
            active=False,
            scale=1.0,
            reason_code="policy_disabled",
            claim_scope=CLAIM_SCOPE,
            modifies_control=False,
            bounded=True,
            notes="Disabled policy returns nominal scale without command shaping.",
        )

    if policy_input.collision or policy_input.qp_infeasible:
        return SlowdownPolicyDecision(
            active=False,
            scale=1.0,
            reason_code="handoff_to_halt_or_recovery",
            claim_scope=CLAIM_SCOPE,
            modifies_control=False,
            bounded=True,
            notes="Slowdown is bypassed; halt or recovery owns this condition.",
        )

    warning_present = any(
        (
            policy_input.dt_warning_any,
            policy_input.h1_warning,
            policy_input.h2_warning,
            policy_input.h3_warning,
        )
    )
    if (
        policy_input.h3_warning
        or policy_input.warning_streak >= config.critical_warning_streak
    ):
        target = config.critical_warning_scale
        reason = "H3_or_critical_warning_streak"
    elif (
        policy_input.h2_warning
        or policy_input.warning_streak >= config.persistent_warning_streak
    ):
        target = config.persistent_warning_scale
        reason = "H2_or_persistent_warning_streak"
    elif (
        policy_input.h1_warning
        or policy_input.dt_warning_any
        or policy_input.warning_streak >= config.enter_warning_streak
    ):
        target = config.warning_scale
        reason = "H1_or_warning_streak"
    elif policy_input.clear_streak >= config.clear_streak_to_release:
        target = 1.0
        reason = "clear_streak_release"
    else:
        target = previous
        reason = "clear_hysteresis_hold"

    scale = _ramp_toward(
        previous, target, config.max_delta_scale_per_step
    )
    scale = min(1.0, max(config.min_scale, scale))
    ramp_bounded = (not previous_valid) or (
        abs(scale - previous)
        <= config.max_delta_scale_per_step + 1e-12
    )
    bounded = (
        config.min_scale <= scale <= 1.0
        and ramp_bounded
    )
    active = scale < 1.0
    modifies_control = active and scale < 1.0 and warning_present
    if not warning_present and active:
        notes = (
            "Policy scale is retained or released under hysteresis; closed-loop "
            "execution must still gate command shaping on a natural warning."
        )
    elif not previous_valid:
        notes = "Invalid previous scale was clamped before bounded policy evaluation."
    else:
        notes = "Bounded warning-streak slowdown decision."
    return SlowdownPolicyDecision(
        active=active,
        scale=scale,
        reason_code=reason,
        claim_scope=CLAIM_SCOPE,
        modifies_control=modifies_control,
        bounded=bounded,
        notes=notes,
    )


def apply_scale_to_vector(u: Any, scale: float) -> Any:
    """Return a scaled copy of a scalar or sequence without importing NumPy."""

    if not math.isfinite(float(scale)):
        raise ValueError("scale must be finite")
    if isinstance(u, list):
        return [apply_scale_to_vector(item, scale) for item in u]
    if isinstance(u, tuple):
        return tuple(apply_scale_to_vector(item, scale) for item in u)
    if isinstance(u, (str, bytes, bytearray)):
        raise TypeError("command vectors cannot be text or byte sequences")
    try:
        return u * scale
    except TypeError as exc:
        try:
            return type(u)(apply_scale_to_vector(item, scale) for item in u)
        except TypeError:
            raise TypeError(f"unsupported command type: {type(u).__name__}") from exc
