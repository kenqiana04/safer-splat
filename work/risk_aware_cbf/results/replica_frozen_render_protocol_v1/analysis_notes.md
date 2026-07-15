# Analysis Notes

The immutable manifest and renderer lock passed before rendering. The renderer
serially produced 300 staging RGB and 300 staging depth files, with no failed
renderer status row. Integrity validation found 33 RGB frames that were fully
black or below the fixed nonzero-pixel threshold and 32 corresponding all-zero
depth frames. These are retained in external staging as failure evidence.

G0.5E-v1 therefore stops at `blocked_by_rgb_integrity`. The staging directory
was not atomically published as `processed/replica/apartment_0`; no frame was
deleted, replaced, resampled, or rendered again.
