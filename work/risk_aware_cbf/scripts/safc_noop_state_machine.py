#!/usr/bin/env python3
"""Passive SAFC state decisions with no control inputs or outputs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SAFCState(str, Enum):
    S0_PreExecutionCertification = "S0_PreExecutionCertification"
    S1_NominalFiltering = "S1_NominalFiltering"
    S2_VerifiedExecution = "S2_VerifiedExecution"
    S3_WarningAwareExecution = "S3_WarningAwareExecution"
    S4_RecoveryMode = "S4_RecoveryMode"
    S5_ReplanRequested = "S5_ReplanRequested"
    S6_SafeHaltAbort = "S6_SafeHaltAbort"


class FeedbackCandidate(str, Enum):
    admit_task = "admit_task"
    no_feedback = "no_feedback"
    command_slowdown_candidate = "command_slowdown_candidate"
    activate_recovery_candidate = "activate_recovery_candidate"
    replan_request_candidate = "replan_request_candidate"
    risk_cost_update_candidate = "risk_cost_update_candidate"
    waypoint_rejection_candidate = "waypoint_rejection_candidate"
    safe_halt_candidate = "safe_halt_candidate"
    diagnostic_only = "diagnostic_only"


class ClaimScope(str, Enum):
    noop_instrumentation_only = "noop_instrumentation_only"
    implemented_supported = "implemented_supported"
    interface_level = "interface_level"
    diagnostic_only = "diagnostic_only"
    unsupported = "unsupported"


@dataclass(frozen=True)
class SAFCEventSnapshot:
    step: int
    trial_id: str
    source: str
    start_certified: Optional[bool] = None
    solver_success: Optional[bool] = None
    qp_infeasible: Optional[bool] = None
    h_current: Optional[float] = None
    h1_warning: Optional[bool] = None
    h2_warning: Optional[bool] = None
    h3_warning: Optional[bool] = None
    dt_warning_any: Optional[bool] = None
    recovery_available: Optional[bool] = None
    recovery_used: Optional[bool] = None
    recovery_success: Optional[bool] = None
    recovery_failed: Optional[bool] = None
    collision: Optional[bool] = None
    progress: Optional[float] = None
    pose_valid: Optional[bool] = None
    map_frame_valid: Optional[bool] = None
    command_adapter_valid: Optional[bool] = None


@dataclass(frozen=True)
class SAFCDecision:
    from_state: SAFCState
    to_state: SAFCState
    feedback_candidate: FeedbackCandidate
    reason_code: str
    claim_scope: ClaimScope
    confidence: str
    no_op: bool = True
    modifies_control: bool = False


def _decision(
    previous_state: SAFCState,
    to_state: SAFCState,
    feedback: FeedbackCandidate,
    reason: str,
    scope: ClaimScope = ClaimScope.noop_instrumentation_only,
    confidence: str = "high",
    from_state: Optional[SAFCState] = None,
) -> SAFCDecision:
    return SAFCDecision(
        from_state=from_state or previous_state,
        to_state=to_state,
        feedback_candidate=feedback,
        reason_code=reason,
        claim_scope=scope,
        confidence=confidence,
    )


def decide_next_state(
    snapshot: SAFCEventSnapshot,
    previous_state: SAFCState,
    warning_streak: int,
    clear_streak: int,
    recovery_streak: int,
) -> SAFCDecision:
    """Return a passive supervisory decision without accepting command vectors."""

    if snapshot.pose_valid is False:
        return _decision(
            previous_state,
            SAFCState.S6_SafeHaltAbort,
            FeedbackCandidate.safe_halt_candidate,
            "pose_invalid",
        )
    if snapshot.map_frame_valid is False:
        return _decision(
            previous_state,
            SAFCState.S6_SafeHaltAbort,
            FeedbackCandidate.safe_halt_candidate,
            "map_frame_invalid",
        )
    if snapshot.command_adapter_valid is False:
        return _decision(
            previous_state,
            SAFCState.S6_SafeHaltAbort,
            FeedbackCandidate.safe_halt_candidate,
            "command_adapter_invalid",
        )
    if snapshot.collision is True:
        return _decision(
            previous_state,
            SAFCState.S6_SafeHaltAbort,
            FeedbackCandidate.safe_halt_candidate,
            "collision_observed",
            ClaimScope.diagnostic_only,
        )
    if snapshot.recovery_failed is True:
        return _decision(
            SAFCState.S4_RecoveryMode,
            SAFCState.S6_SafeHaltAbort,
            FeedbackCandidate.safe_halt_candidate,
            "recovery_failed",
            from_state=SAFCState.S4_RecoveryMode,
        )

    if previous_state == SAFCState.S0_PreExecutionCertification:
        if snapshot.start_certified is True:
            return _decision(
                previous_state,
                SAFCState.S1_NominalFiltering,
                FeedbackCandidate.admit_task,
                "start_certified",
            )
        if snapshot.start_certified is False:
            return _decision(
                previous_state,
                SAFCState.S6_SafeHaltAbort,
                FeedbackCandidate.safe_halt_candidate,
                "start_not_certified",
            )
        return _decision(
            previous_state,
            previous_state,
            FeedbackCandidate.diagnostic_only,
            "start_status_unavailable",
            ClaimScope.unsupported,
            "low",
        )

    if snapshot.qp_infeasible is True or snapshot.solver_success is False:
        if snapshot.recovery_available is True:
            return _decision(
                previous_state,
                SAFCState.S4_RecoveryMode,
                FeedbackCandidate.activate_recovery_candidate,
                "qp_infeasible_recovery_available",
            )
        return _decision(
            previous_state,
            SAFCState.S6_SafeHaltAbort,
            FeedbackCandidate.safe_halt_candidate,
            "qp_infeasible_no_recovery",
        )

    if snapshot.recovery_used is True:
        if snapshot.recovery_success is True:
            return _decision(
                SAFCState.S4_RecoveryMode,
                SAFCState.S2_VerifiedExecution,
                FeedbackCandidate.no_feedback,
                "recovery_success_reverified",
                ClaimScope.implemented_supported,
                from_state=SAFCState.S4_RecoveryMode,
            )
        if recovery_streak >= 3:
            return _decision(
                SAFCState.S4_RecoveryMode,
                SAFCState.S5_ReplanRequested,
                FeedbackCandidate.replan_request_candidate,
                "repeated_recovery",
                ClaimScope.interface_level,
                "medium",
                from_state=SAFCState.S4_RecoveryMode,
            )
        return _decision(
            previous_state,
            SAFCState.S4_RecoveryMode,
            FeedbackCandidate.activate_recovery_candidate,
            "recovery_in_progress",
        )

    warning = any(
        item is True
        for item in (
            snapshot.dt_warning_any,
            snapshot.h1_warning,
            snapshot.h2_warning,
            snapshot.h3_warning,
        )
    )
    if warning:
        if warning_streak >= 3:
            return _decision(
                previous_state,
                SAFCState.S5_ReplanRequested,
                FeedbackCandidate.replan_request_candidate,
                "persistent_warning",
                ClaimScope.interface_level,
                "medium",
            )
        if snapshot.recovery_available is True:
            return _decision(
                previous_state,
                SAFCState.S3_WarningAwareExecution,
                FeedbackCandidate.activate_recovery_candidate,
                "dt_warning_recovery_candidate",
            )
        return _decision(
            previous_state,
            SAFCState.S3_WarningAwareExecution,
            FeedbackCandidate.command_slowdown_candidate,
            "dt_warning_no_recovery",
        )

    if snapshot.solver_success is True:
        return _decision(
            previous_state,
            SAFCState.S2_VerifiedExecution,
            FeedbackCandidate.no_feedback,
            "qp_success_no_warning",
        )

    return _decision(
        previous_state,
        previous_state,
        FeedbackCandidate.diagnostic_only,
        "insufficient_snapshot_evidence",
        ClaimScope.unsupported,
        "low",
    )
