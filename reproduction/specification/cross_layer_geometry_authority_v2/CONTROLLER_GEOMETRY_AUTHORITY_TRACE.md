# Controller Geometry Authority Trace

Authority `G0 = CONTROLLER_GEOMETRY_AUTHORITY` originates in `run.py:47-50`, where the Stonehenge branch fixes `radius = 0.015`. `run.py:115` injects that value into `CBF`. `cbf/cbf_utils.py:11-21` stores it, and `cbf/cbf_utils.py:45` supplies it to the represented-map `query_distance` call.

The controller therefore owns `r_controller=0.015 m`. V2 does not change this value or add the certification margin to the active controller. The active controller query remains a ball-to-ellipsoid query over the frozen represented map.

Resolution failure rule: if G0 cannot be resolved from the frozen runtime/config authority, certification returns `UNKNOWN/BLOCK`; it must not substitute `0.10` or `0.11` from a historical V1 artifact.
