# TUM Map Geometry Root-Cause and Repair V1

Result: `ROOT_CAUSE_IDENTIFIED_BUT_NO_REPAIR_CANDIDATE_QUALIFIED`.

The frozen V1R6 checkpoint/config/transforms identities all matched.  The 300
frame RGB-D chain is consistent: depth is uint16 TUM 1/5000 encoding, RGB and
depth are registered at 640x480, intrinsics are consistent, and the fixed
adjacent-frame reprojections have median residuals of 0.003--0.012 m.

V1R6 was confirmed to use random initialization: dataparser metadata had no
`points3D_xyz`/`points3D_rgb`, so stock Splatfacto used 50,000 random points at
random scale 10.  Its stock training objective was RGB-only, with no GT-depth
loss.  The native comparison semantic was expected depth (`RGB+ED`); no
alternative native accumulated/normalized/median/first depth output was used
as a substitution.

The deterministic 240-frame RGB-D seed contained 359,140 points (NPZ SHA-256
`c5d69bbc965f16147842ad9813eca6d41d9556dd6af602e5b5049402a12e8b56`).
Depth supervision used fixed metric Smooth-L1, lambda 0.10, beta 0.10, and an
accumulation mask; smoke logs confirmed the depth loss and valid-depth ratio.

At 3k, C1 (seed only) failed. C2 (depth only) reached AbsRel 0.399/delta1
0.388, and C3 (seed plus depth) won the preregistered ordering at AbsRel 0.333,
delta1 0.457, ratio 1.004. C3 was retrained from scratch for 10k, not resumed.
Its fixed-60 raw metrics were overlap 1.0, AbsRel 0.344, RMSE 0.741, delta1
0.448/delta2 0.681/delta3 0.799, and ratio 0.915. It had 423,520 Gaussians,
zero nonfinite values and zero invalid covariances. A static 908-point SAFER
map query was finite, had finite gradients, and exactly repeated; it used no
controller, dynamics, QP, navigation, or G1.

This is a major improvement over V1R6 (AbsRel 0.791, delta1 0.062, ratio
0.170), supporting `RANDOM_INITIALIZATION_PLUS_RGB_ONLY_SUPERVISION` as the
primary root cause.  It nevertheless fails the internal G0 gate because
delta1 is below 0.50 and AbsRel is above the acceptable 0.25 threshold.
Accordingly no formal repair protocol is frozen. No formal training, V1R7,
SAFER navigation, CBF-QP, rollout, or G1 was run.
