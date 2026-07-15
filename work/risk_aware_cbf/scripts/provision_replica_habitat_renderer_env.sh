#!/usr/bin/env bash
set -euo pipefail
# Query only: G0.5D requires an official Python 3.12 Habitat-Sim 0.3.3 binary.
conda search habitat-sim=0.3.3 -c conda-forge -c aihabitat --info
echo 'Refuse installation unless an official Python 3.12 compatible headless build is resolved.'
