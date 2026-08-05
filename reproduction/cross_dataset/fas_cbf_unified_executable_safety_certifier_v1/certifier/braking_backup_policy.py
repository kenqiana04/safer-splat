"""Deterministic componentwise non-reversing braking policy."""
from __future__ import annotations

import math

from .result_types import ActuatorBounds, Control, State


class ZeroActuatorAuthority(RuntimeError):
    pass


class DeterministicBrakingPolicy:
    identity="DETERMINISTIC_COMPONENTWISE_BRAKING_POLICY_V1"

    def __init__(self,bounds:ActuatorBounds,velocity_tolerance:float)->None:
        if not bounds.valid: raise ValueError("INVALID_ACTUATOR_BOUNDS")
        self.bounds=bounds; self.velocity_tolerance=float(velocity_tolerance)

    def control_for_state(self,state:State,step:int=0)->Control:
        acceleration=[]
        for i,velocity in enumerate(state.velocity):
            if abs(velocity)<=self.velocity_tolerance:
                acceleration.append(0.0); continue
            if velocity>0.0:
                authority=-self.bounds.u_min[i]
                if authority<=0.0: raise ZeroActuatorAuthority(f"ZERO_NEGATIVE_AUTHORITY_AXIS_{i}")
                magnitude=min(authority,velocity/self.bounds.dt)
                acceleration.append(-magnitude)
            else:
                authority=self.bounds.u_max[i]
                if authority<=0.0: raise ZeroActuatorAuthority(f"ZERO_POSITIVE_AUTHORITY_AXIS_{i}")
                magnitude=min(authority,-velocity/self.bounds.dt)
                acceleration.append(magnitude)
        return Control(tuple(acceleration),"DETERMINISTIC_BRAKING_BACKUP",f"brake-{step:04d}")

    def h_stop(self,state:State)->int:
        horizons=[]
        for i,velocity in enumerate(state.velocity):
            if abs(velocity)<=self.velocity_tolerance:
                horizons.append(0); continue
            authority=-self.bounds.u_min[i] if velocity>0 else self.bounds.u_max[i]
            if authority<=0.0: raise ZeroActuatorAuthority(f"ZERO_BRAKE_AUTHORITY_AXIS_{i}")
            horizons.append(int(math.ceil(abs(velocity)/(authority*self.bounds.dt))))
        return max(horizons,default=0)

    def h_stop_max(self)->int:
        horizons=[]
        for i in range(3):
            speed=max(abs(self.bounds.v_min[i]),abs(self.bounds.v_max[i]))
            authority=min(-self.bounds.u_min[i],self.bounds.u_max[i])
            if speed>0.0 and authority<=0.0: raise ZeroActuatorAuthority(f"ZERO_GLOBAL_BRAKE_AUTHORITY_AXIS_{i}")
            horizons.append(0 if speed==0.0 else int(math.ceil(speed/(authority*self.bounds.dt))))
        return max(horizons,default=0)
