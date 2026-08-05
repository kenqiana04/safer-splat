"""Normative swept-position segment certification facade."""
from __future__ import annotations

import numpy as np

from adapters.normative_dynamics_adapter import PositionFirstForwardEulerDoubleIntegrator
from .result_types import Control, SegmentCertificate, State


class SweptSegmentCertifier:
    def __init__(self,dynamics:PositionFirstForwardEulerDoubleIntegrator,backend:object,effective_radius:float,rho_seg:float=0.0)->None:
        self.dynamics=dynamics; self.backend=backend; self.effective_radius=float(effective_radius); self.rho_seg=float(rho_seg)

    def certify(self,state:State,control:Control,expected_snapshot_id:str)->SegmentCertificate:
        # In the normative model the immediate position segment is independent
        # of acceleration. Control remains explicit to prevent model ambiguity.
        start,end=self.dynamics.segment_endpoints(state)
        return self.backend.certify(np.asarray(start),np.asarray(end),state.map_snapshot_id,expected_snapshot_id,self.effective_radius,self.rho_seg)
