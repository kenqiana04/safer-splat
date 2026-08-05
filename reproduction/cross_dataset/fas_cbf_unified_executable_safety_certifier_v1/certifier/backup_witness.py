"""Backup witness helper invariants."""
from __future__ import annotations

from .result_types import BackupWitness


def tail_witness_is_structurally_valid(witness:BackupWitness)->bool:
    if not witness.certified or witness.terminal_certificate is None or not witness.terminal_certificate.certified:
        return False
    return (
        len(witness.states)==len(witness.backup_controls)+3
        and len(witness.per_segment_certificates)==len(witness.backup_controls)+2
        and all(c.certified for c in witness.per_segment_certificates)
        and all(s.map_snapshot_id==witness.map_snapshot_id for s in witness.states)
    )


def tail_from(witness:BackupWitness,index:int)->dict:
    if not tail_witness_is_structurally_valid(witness): raise ValueError("INVALID_WITNESS")
    if index<0 or index>len(witness.backup_controls): raise IndexError(index)
    return {
        "state":witness.states[index+1].to_dict(),
        "remaining_controls":[c.to_dict() for c in witness.backup_controls[index:]],
        "remaining_segments":[c.to_dict() for c in witness.per_segment_certificates[index+1:]],
        "terminal_certificate":witness.terminal_certificate.to_dict(),
        "assumptions":["SAME_MAP_SNAPSHOT","EXACT_PREDICTED_STATE","NO_DELAY_DISTURBANCE_OR_TRACKING_ERROR"],
    }
