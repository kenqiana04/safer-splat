# Next Step After Replica Python 3.9 Closure

G0.5D-v2 resolved the official renderer-environment gate and passed an
official-mesh RGB/depth/navmesh smoke. Before formal preprocessing, create and
freeze a separate Replica render protocol containing the camera trajectory,
seed, 300-frame selection rule, pose convention, and train/eval split. That
task must reuse `apartment_0`; it must not reselect a scene based on smoke or
rendering quality.

No Gaussian training or SAFER execution is authorized by this closure.
