#!/usr/bin/env bash
set -euo pipefail

# G0.5D-v2: query and solve only against the official stable channels.
CONDA_BIN="${CONDA_BIN:-conda}"
ENV_NAME="replica_habitat_renderer_py39"
BUILD="py3.9_headless_bullet_linux_acbe6f4922e68145e401e55c30f9dfea460a3f24"

"${CONDA_BIN}" search habitat-sim=0.3.3 -c conda-forge -c aihabitat --info
"${CONDA_BIN}" create --dry-run --override-channels -n "${ENV_NAME}" \
  python=3.9 numpy pillow imageio pyyaml -c conda-forge
"${CONDA_BIN}" create --dry-run --override-channels -n "${ENV_NAME}" \
  python=3.9 numpy pillow imageio pyyaml "habitat-sim=0.3.3=${BUILD}" \
  -c conda-forge -c aihabitat

echo "Create only after reviewing the two successful dry-run plans."
