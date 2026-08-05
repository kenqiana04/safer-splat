from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

TASK_ROOT=Path(__file__).resolve().parents[1]
if str(TASK_ROOT) not in sys.path: sys.path.insert(0,str(TASK_ROOT))

from adapters.current_cbf_adapter import CurrentCBFAdapter
from adapters.gaussian_barrier_adapter import AnalyticSphereGaussianMapAdapter
from adapters.normative_dynamics_adapter import PositionFirstForwardEulerDoubleIntegrator
from certifier.backup_certifier import BackupCertifier
from certifier.braking_backup_policy import DeterministicBrakingPolicy
from certifier.executable_safety_certifier import ExecutableSafetyCertifier
from certifier.result_types import ActuatorBounds,Control,State
from certifier.segment_certificate import SweptSegmentCertifier
from certifier.terminal_certificate import TerminalCertifier
from certifier.terminal_set import BrakingToRestTerminalSet


@pytest.fixture
def bounds():
    return ActuatorBounds((-0.5,)*3,(0.5,)*3,(-1.0,)*3,(1.0,)*3,0.1)


def build_stack(centers=((100.0,100.0,100.0),),primitive_radius=0.1,effective_radius=0.2,snapshot="map-v1",bounds=None,velocity_tolerance=1e-12):
    if bounds is None: bounds=ActuatorBounds((-0.5,)*3,(0.5,)*3,(-1.0,)*3,(1.0,)*3,0.1)
    adapter=AnalyticSphereGaussianMapAdapter(np.asarray(centers,dtype=float),primitive_radius,snapshot,effective_radius)
    dynamics=PositionFirstForwardEulerDoubleIntegrator(bounds)
    segment=SweptSegmentCertifier(dynamics,adapter.segment_backend,effective_radius)
    current=CurrentCBFAdapter(adapter)
    terminal_set=BrakingToRestTerminalSet(velocity_tolerance)
    terminal=TerminalCertifier(terminal_set,current,segment)
    policy=DeterministicBrakingPolicy(bounds,velocity_tolerance)
    backup=BackupCertifier(dynamics,segment,terminal,policy)
    unified=ExecutableSafetyCertifier(current,segment,terminal,backup,policy,{"map_snapshot_id":snapshot,"execution_model":dynamics.identity})
    return {"adapter":adapter,"dynamics":dynamics,"segment":segment,"current":current,"terminal":terminal,"policy":policy,"backup":backup,"unified":unified,"bounds":bounds}


@pytest.fixture
def free_stack(bounds):
    return build_stack(bounds=bounds)


@pytest.fixture
def moving_state():
    return State((0.0,0.0,0.0),(0.2,0.0,0.0),0.0,"map-v1")


@pytest.fixture
def zero_state():
    return State((0.0,0.0,0.0),(0.0,0.0,0.0),0.0,"map-v1")
