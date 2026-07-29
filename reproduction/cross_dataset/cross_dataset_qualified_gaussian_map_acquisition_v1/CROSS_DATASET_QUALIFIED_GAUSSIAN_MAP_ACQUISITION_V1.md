# Cross-Dataset Qualified Gaussian Map Acquisition, Qualification and Selection V1

This task is a bounded acquisition and qualification gate.  It preserves the
frozen negative or limited mapping-route findings and separates them from the
question of whether SAFER can be statically evaluated on independent,
pretrained Gaussian maps.

## Execution plan

1. Freeze the TUM, Splatfacto, SplaTAM, Gaussian-SLAM, and Replica-V3 route
   decisions without invoking any training or navigation path.
2. Inventory the official SAFER assets and run only checkpoint load plus static
   G0 queries for assets that are actually present.
3. Verify public-source access before downloading any external scene payload.
   The primary family is Hypersim through GaussianWorld; ARKitScenes is a
   frozen fallback only after the stated primary failure conditions.
4. If access is unavailable, write explicit gate-bound artifacts for every
   downstream stage rather than inventing candidate, geometry, or G0 results.
5. Validate the compact evidence, figures, and handoff; no training,
   filtering, scale fitting, Sim(3), ICP, controller, CBF-QP, or navigation is
   authorized by this task.

The remote executable is `audit_cross_dataset_map.py`.  It uses a single
atomic JSON writer and writes only under the task-owned maintenance root.  Its
static official G0 routine uses `GSplatLoader` in inference mode, performs 32
deterministic distance/gradient/Hessian queries three times, and does not call
controller or navigation code.
