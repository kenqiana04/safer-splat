# TUM Splatfacto Conda Activation Strict-Mode Correction V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute this preregistered correction inline, one gate at a time. Do not launch training.

**Goal:** Move nounset activation until immediately after Conda activation,
prove the old failure and corrected activation-only behavior, and regenerate
the canonical protocol identity without changing training semantics.

**Architecture:** The only behavioral code change is the strict-mode ordering
in `exact_training_command.sh`. Server probes use isolated noninteractive
subshells and never invoke the `splatfacto` training command.

**Tech Stack:** Git blobs, Bash strict mode, Conda, Python AST, and GitHub PR
evidence.

---

## Observed failure

- Evidence PR: #27, `BLOCKED_BY_LAUNCH_WRAPPER`, attempt count 0.
- The tmux wrapper was briefly created; `ns-train` never appeared.
- The frozen script exited 1 in `deactivate-gfortran_linux-64.sh` because
  `GFORTRAN` was unbound under pre-activation nounset.
- Root cause: `CONDA_ACTIVATION_INCOMPATIBLE_WITH_PRE_ACTIVATION_NOUNSET`.

## Frozen correction

The sole allowed behavior change is:

```bash
set -euo pipefail
source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat_official
```

becoming:

```bash
set -eo pipefail
source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat_official
set -u
```

No variable patch, Conda hook change, environment change, or training-argument
change is allowed.

## Task 1: Reproduce before-state activation only

- [ ] Run the old strict-mode ordering in `bash --noprofile --norc`.
- [ ] Record a nonzero exit, the failing hook, and unbound variable; do not
  invoke `ns-train`.

## Task 2: Apply and compare the correction

- [ ] Change only the strict-mode lines before/after `conda activate`.
- [ ] Compare old Git-blob and current `ns-train` tokens with `shlex.split`.
- [ ] Require zero training-argument differences and zero config changes.

## Task 3: Verify corrected activation only

- [ ] Run `bash -n`, Conda activation, Python version, `ns-train --help`,
  `ns-eval --help`, and `ns-render dataset --help` only.
- [ ] Require no CUDA training process, run directory, checkpoint, eval, or
  render.

## Task 4: Rebuild canonical identity and publish evidence

- [ ] Commit the correction, derive command SHA-256 from raw Git blob bytes,
  verify a clean detached server checkout, and update protocol metadata.
- [ ] Run validators, update PR #23 and the immutable PR #27 comment, copy
  the report, and stop without authorizing training.

## Semantic immutability

The `ns-train` executable, method, output path, timestamp, seed, device,
iterations, precision, save/eval cadence, camera optimizer, Gaussian model
arguments, parser, dataset, 240/60 split, and depth scale must remain exactly
unchanged. `frozen_training_config.json` must have no byte change.
