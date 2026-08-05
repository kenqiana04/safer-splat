"""Frozen candidate provenance and deterministic order."""
from __future__ import annotations

from .braking_backup_policy import DeterministicBrakingPolicy,ZeroActuatorAuthority
from .result_types import Control,State


def frozen_candidate_order(state:State,nominal:Control,alternatives:tuple[Control,...],braking_policy:DeterministicBrakingPolicy)->tuple[Control,...]:
    existing=tuple(sorted((c for c in alternatives if c.source=="EXISTING_CBF_FILTERED"),key=lambda c:c.candidate_id))
    task_local=tuple(sorted((c for c in alternatives if c.source!="EXISTING_CBF_FILTERED"),key=lambda c:c.candidate_id))
    result=[nominal,*existing,*task_local]
    try: result.append(braking_policy.control_for_state(state,-1))
    except ZeroActuatorAuthority: pass
    seen=set(); unique=[]
    for candidate in result:
        if candidate.candidate_id not in seen:
            seen.add(candidate.candidate_id); unique.append(candidate)
    return tuple(unique)
