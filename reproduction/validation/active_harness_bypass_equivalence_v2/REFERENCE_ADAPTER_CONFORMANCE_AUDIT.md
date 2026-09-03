# Reference Adapter Conformance Audit

**Verdict: PASS_REFERENCE_CONTROL_PLANT_PATH_SOURCE_LOCK**

The task-local adapter is Option B because the repository has no selected-trial runner that both invokes the new PR #116 BYPASS path and exposes the required exact per-step comparison schema. It reproduces only the following protected `run.py` slice and does not edit or execute a rewritten production file.

| Frozen semantic | Protected source | Adapter binding |
|---|---|---|
| 100-point configuration | `run.py:20,26-27,84-96` | NumPy `linspace`, radii, mean, starts, and antipodal goals are expression-identical. |
| State/goal initialization | `run.py:101-104` | selected row converted to CUDA float32 and concatenated with zero velocity. |
| PD desired command | `run.py:118-127` | gains 5.0/1.0 and both componentwise clamps are expression-identical. |
| CBF-QP | `run.py:114-137` | fresh `CBF(gsplat, dynamics,5,1,0.015,ball-to-ellipsoid)` and `solve_QP`; solver-failure branch stops before commit. |
| Plant | `run.py:145-147` | `double_integrator_dynamics(x,u)*0.05+x` on the same CUDA float32 device. |
| Native termination | `run.py:163-177` | exact not-moving threshold, pre-state goal check, and 500-step moving timeout branch. |

The legacy post-propagation `safety` query and `sucess/feasible` labels are deliberately omitted because they are scientific/legacy diagnostics rather than control or plant inputs. The adapter reports native termination names and no collision, progress, success, L1, L2, or L3 outcome.

Static Q0 tests lock the protected source blob, constants, trial construction, source expressions, and absence of active/oracle imports from the reference path.
