# TUM G0 Audit Correction Preregistration V1

## Correction Scope

This correction is limited to source-backed TUM Freiburg 1 depth unit/scale
provenance and dataparser audit post-processing shape handling. It does not
modify raw data, processed data, `transforms.json`, poses, frame association,
Nerfstudio packages, core code, or any training/checkpoint/SAFER behavior.

## Dataparser Bug Hypothesis

The earlier audit observed:

```text
RuntimeError: The size of tensor a (3) must match the size of tensor b (4)
```

This audit tests, without presuming, whether Nerfstudio exposes a `3x4`
`dataparser_transform` while the audit compared it with `torch.eye(4)`, and
whether that exception occurred in audit post-processing rather than in parser
output generation.

## Fixed Correction Rule

For `transform = train.dataparser_transform`, the identity reference is:

```python
if tuple(transform.shape) == (3, 4):
    expected_identity = torch.eye(4, dtype=transform.dtype, device=transform.device)[:3, :]
elif tuple(transform.shape) == (4, 4):
    expected_identity = torch.eye(4, dtype=transform.dtype, device=transform.device)
else:
    raise DataparserTransformShapeError(tuple(transform.shape))
```

No reshape, padding, flattening, truncation outside this rule, or coercion of
an unexpected shape is permitted. The preregistered scale tolerance is
`abs(dataparser_scale - 1.0) <= 1e-9`.

## Depth Source Contract Expectations

The TUM official page must establish, before use: 640x480 16-bit monochrome
PNG depth; 5000 depth units per meter; `depth_m = depth_raw / 5000.0`; zero as
missing/no-data; Freiburg 1's 1.035 correction already applied by the dataset
provider; and no additional 1.035 correction. These statements remain pending
until a TUM official URL, retrieval time, page hash, and structured extraction
are recorded.

## Fixed Pass Conditions

Depth closure requires an exact `rgbd_dataset_freiburg1_room` identity, readable
official contract, all 300 selected depths mapped to raw sources, byte identity
or direct reference for each, no preprocessor scaling/re-encoding, no repeated
1.035 correction, exactly one future `1/5000` conversion, and no double scaling.

Dataparser closure requires successful train and val outputs, stage-resolved
evidence, permitted transform shape, shape-compatible identity, 300 parsed
frames with no drop, complete filename pose mapping, no orientation/centering
change, actual translation ratio near one, and no model/trainer/optimizer/
checkpoint/viewer.

## Decision States

`PASS_DEPTH_AND_DATAPARSER_CORRECTION`, `BLOCKED_BY_OFFICIAL_SOURCE_UNAVAILABLE`,
`BLOCKED_BY_DEPTH_COPY_MISMATCH`, `BLOCKED_BY_DEPTH_DOUBLE_SCALING_RISK`,
`BLOCKED_BY_DATAPARSER_GENERATION`, `BLOCKED_BY_DATAPARSER_POSTPROCESS`,
`BLOCKED_BY_DATAPARSER_TRANSFORM_SHAPE`, `BLOCKED_BY_POSE_MAPPING`,
`BLOCKED_BY_CRITICAL_PROVENANCE`, and `FAIL` are the only correction outcomes.
