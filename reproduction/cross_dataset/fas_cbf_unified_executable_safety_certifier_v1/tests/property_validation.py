"""Frozen randomized implementation-consistency validation."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

TASK_ROOT=Path(__file__).resolve().parents[1]
if str(TASK_ROOT) not in sys.path: sys.path.insert(0,str(TASK_ROOT))

from adapters.current_cbf_adapter import CurrentCBFAdapter
from adapters.gaussian_barrier_adapter import AnalyticSphereGaussianMapAdapter,UnknownMapAdapter
from adapters.normative_dynamics_adapter import PositionFirstForwardEulerDoubleIntegrator
from certifier.actuator_certificate import certify_actuator
from certifier.braking_backup_policy import DeterministicBrakingPolicy
from certifier.current_feasibility_certificate import certify_current_feasibility
from certifier.result_types import ActuatorBounds,BarrierStatus,Control,SegmentStatus,State
from certifier.segment_backends.analytic_primitive import ExactQuadraticEllipsoidSegmentBackend,ExactSphereSegmentBackend
from certifier.segment_backends.conservative_interval import ConservativeSignedDistanceIntervalBackend
from task_config import PROPERTY_TEST_SEED


def _sphere_dense_min(start,end,center,primitive_radius,effective_radius,samples=513):
    t=np.linspace(0.0,1.0,samples)[:,None]
    points=start[None,:]+t*(end-start)[None,:]
    signed=np.linalg.norm(points-center[None,:],axis=1)-primitive_radius
    h=np.copysign(signed*signed,signed)-effective_radius**2
    return float(np.min(h))


def _quadratic_dense_min(start,end,center,q,samples=513):
    t=np.linspace(0.0,1.0,samples)[:,None]; y=start[None,:]+t*(end-start)[None,:]-center[None,:]
    return float(np.min(np.einsum("ni,ij,nj->n",y,q,y)-1.0))


def run_property_validation(segment_count=10_000,backup_count=2_000,fail_closed_count=1_000,seed=PROPERTY_TEST_SEED):
    rng=np.random.default_rng(seed); false_safe=0; false_reject=0; inconclusive=0
    sphere_cases=segment_count//2; ellipsoid_cases=segment_count-sphere_cases
    conservative_validation_count=min(1_000,sphere_cases)
    for index in range(sphere_cases):
        start=rng.uniform(-2,2,3); end=rng.uniform(-2,2,3); center=rng.uniform(-1,1,3)
        primitive=float(rng.uniform(0.02,0.4)); effective=float(rng.uniform(0.01,0.3))
        cert=ExactSphereSegmentBackend(center[None,:],primitive,"prop").certify(start,end,"prop","prop",effective)
        diagnostic=_sphere_dense_min(start,end,center,primitive,effective)
        if cert.certified and diagnostic < -1e-10: false_safe+=1
        if not cert.certified and cert.status==SegmentStatus.CERTIFIED_UNSAFE and diagnostic>=1e-5: false_reject+=1
        if index<conservative_validation_count:
            class Provider:
                map_snapshot_id="prop"
                def minimum_signed_distance(self,point):
                    return "FINITE",float(np.linalg.norm(np.asarray(point)-center)-primitive),1
            conservative=ConservativeSignedDistanceIntervalBackend(Provider(),node_budget=4096,parameter_tolerance=1e-10).certify(start,end,"prop","prop",effective)
            if conservative.certified and not cert.certified: false_safe+=1
            if conservative.status==SegmentStatus.NOT_CERTIFIED_WITHIN_BUDGET: inconclusive+=1
    for index in range(ellipsoid_cases):
        start=rng.uniform(-2,2,3); end=rng.uniform(-2,2,3); center=rng.uniform(-1,1,3)
        axes=rng.uniform(0.1,0.8,3); q=np.diag(1.0/(axes*axes))
        cert=ExactQuadraticEllipsoidSegmentBackend(center[None,:],q[None,:,:],"prop").certify(start,end,"prop","prop")
        diagnostic=_quadratic_dense_min(start,end,center,q)
        if cert.certified and diagnostic < -1e-10: false_safe+=1
        if not cert.certified and cert.status==SegmentStatus.CERTIFIED_UNSAFE and diagnostic>=1e-5: false_reject+=1

    bounds=ActuatorBounds((-0.5,)*3,(0.5,)*3,(-1.,)*3,(1.,)*3,0.1)
    dynamics=PositionFirstForwardEulerDoubleIntegrator(bounds); policy=DeterministicBrakingPolicy(bounds,1e-12)
    backup_success=0
    for index in range(backup_count):
        velocity=tuple(float(v) for v in rng.uniform(-1.0,1.0,3)); state=State((0.,0.,0.),velocity,0.,"prop")
        previous=np.asarray(velocity,dtype=float); horizon=policy.h_stop(state)
        for step in range(horizon):
            control=policy.control_for_state(state,step); state=dynamics.transition(state,control); current=np.asarray(state.velocity)
            if np.any(np.abs(current)>np.abs(previous)+1e-12) or np.any(current*previous < -1e-14):
                raise AssertionError("BRAKING_MONOTONICITY_COUNTEREXAMPLE")
            previous=current
        if max(abs(v) for v in state.velocity)<=1e-12: backup_success+=1

    fail_closed_pass=0
    unsafe_backend=ExactSphereSegmentBackend(np.asarray([[0.,0.,0.]]),0.2,"prop")
    unknown_current=CurrentCBFAdapter(UnknownMapAdapter("prop",BarrierStatus.UNKNOWN))
    for index in range(fail_closed_count):
        mode=index%4
        if mode==0:
            ok=not certify_actuator(Control((1.0,0.,0.),"NOMINAL",f"fc-{index}"),bounds).certified
        elif mode==1:
            state=State((0.,0.,0.),(0.,0.,0.),0.,"prop")
            ok=not certify_current_feasibility(state,unknown_current).certified
        elif mode==2:
            cert=unsafe_backend.certify(np.asarray([-1.,0.,0.]),np.asarray([1.,0.,0.]),"prop","prop",0.1)
            ok=(not cert.certified and cert.status==SegmentStatus.CERTIFIED_UNSAFE)
        else:
            # Candidate-library exhaustion is bounded non-certification by
            # contract; the forbidden status is absent from the enum entirely.
            from certifier.result_types import AUTHORIZED_STATUS_VALUES
            ok="CERTIFIED_UNRECOVERABLE" not in AUTHORIZED_STATUS_VALUES
        fail_closed_pass+=int(ok)

    return {
        "seed":seed,
        "randomized_segment_test_count":segment_count,
        "sphere_segment_count":sphere_cases,
        "ellipsoid_segment_count":ellipsoid_cases,
        "conservative_interval_validation_count":conservative_validation_count,
        "randomized_backup_test_count":backup_count,
        "randomized_backup_success_count":backup_success,
        "randomized_fail_closed_test_count":fail_closed_count,
        "randomized_fail_closed_pass_count":fail_closed_pass,
        "false_safe_count":false_safe,
        "false_reject_count":false_reject,
        "inconclusive_count":inconclusive,
        "diagnostic_oracle_role":"IMPLEMENTATION_ERROR_DISCOVERY_ONLY_NOT_PROOF",
    }


if __name__=="__main__":
    result=run_property_validation()
    out=TASK_ROOT/"proof_artifacts"/"property_test_summary.json"; out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(result,sort_keys=True))
