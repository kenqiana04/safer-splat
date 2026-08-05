import json
import math
from certifier.actuator_certificate import certify_actuator,clipped_alternative
from certifier.result_types import ActuatorBounds,Control


def test_boundary_inclusive_and_just_outside_rejected(bounds):
    assert certify_actuator(Control(bounds.u_max,"N","b"),bounds).certified
    assert not certify_actuator(Control((bounds.u_max[0]+1e-12,0.,0.),"N","o"),bounds).certified


def test_nonfinite_and_clipping_provenance(bounds):
    assert not certify_actuator(Control((math.nan,0.,0.),"N","bad"),bounds).certified
    clipped=clipped_alternative(Control((2.,0.,0.),"N","raw"),bounds,"clip-1")
    assert clipped.acceleration[0]==bounds.u_max[0]
    assert clipped.candidate_id=="clip-1" and "raw" in clipped.source
    assert certify_actuator(clipped,bounds).certified
    assert clipped.to_json()==clipped.to_json()
    json.loads(clipped.to_json())
