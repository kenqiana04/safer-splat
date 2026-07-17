# TUM Splatfacto Config Selection Policy Preregistration V1

## Protocol Objective

This protocol freezes one reproducible, no-tuning `TUM_FR1_ROOM` standard
`splatfacto` training configuration for a later G0 checkpoint candidate. It
does not optimize TUM PSNR, SSIM, LPIPS, loss, runtime, Gaussian count, SAFER,
or navigation outcomes.

## No-Tuning Rule

V1 permits one formal configuration, seed `20260716`, and fraction split
`0.8`. After formal execution, no parameter may be changed in response to
quality, loss, runtime, geometry, SAFER, or navigation outcomes. Any changed
configuration is V2 and must be reported separately.

## Parameter Source Precedence

1. The immutable PR #22 metric-data contract controls data path, transforms
   hash, 240/60 split, `orientation_method=none`, `center_method=none`,
   `auto_scale_poses=false`, `downscale_factor=1`,
   `depth_unit_scale_factor=0.0002`, parser scale one, no COLMAP, and no pose
   normalization. Reference configs cannot override these fields.
2. The Stonehenge comparator reconstruction config at
   `outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml` is the primary
   source for method, model, optimizer, scheduler, and training-budget values.
3. The Flight config at
   `outputs/flight/splatfacto/2024-09-12_172434/config.yml` is a secondary
   comparison only.
4. Nerfstudio 1.1.5 schema/defaults may fill only fields absent from both
   reference configs.

If Stonehenge and Flight differ, V1 uses the Stonehenge value and records the
Flight value; averaging, compromise, or TUM-outcome selection is prohibited.
If a legacy field cannot be mapped to Nerfstudio 1.1.5 with demonstrated
semantic equivalence, V1 is `BLOCKED_BY_REFERENCE_CONFIG_INCOMPATIBILITY`.

## Dataset-Specific Overrides

Only data/output paths, experiment/run name, seed, split, metric-preserving
parser fields, depth scale, viewer state, GPU selection, and log/checkpoint
paths may differ from the primary reference. TUM scene size, image count, or
visual appearance cannot justify changes to iterations, learning rates,
densification, pruning, opacity, SH degree, refinement, Gaussian cap,
regularization, or loss weights.

## Method, Depth, and Checkpoint Boundaries

The only method is installed standard `splatfacto`; variants and modified model
configs are prohibited. Whether standard Splatfacto uses depth is an audit
question, not authorization to switch methods or enable an extra loss. The
future meter conversion is exactly one `1/5000=0.0002` scale, with no extra
Freiburg1 `1.035` correction.

The only formal checkpoint may be the exact final checkpoint at frozen maximum
iterations. Metric, visual, multi-seed, or early-checkpoint selection is
prohibited. Incomplete runs are not eligible substitutes.

## Stop Conditions

Protocol construction stops if the primary reference cannot be read, its hash
cannot be recorded, a required parameter lacks provenance, schema equivalence
cannot be demonstrated, or the metric-data contract is inconsistent. This
preregistration authorizes neither training nor a checkpoint, SAFER, or G1.
