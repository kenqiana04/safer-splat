# Risk-Aware CBF Reproducibility Manifest

## Repository audit notes

This file records which artifacts are intended to remain version controlled.

## Tracked artifacts

- Method and experiment reports under `work/risk_aware_cbf/`
- Paper positioning documents
- Decision notes
- Analysis summaries

## Recommended tracked execution artifacts

- Key analysis scripts under `work/risk_aware_cbf/scripts/`
- Small summary files such as CSV metrics and JSON summaries
- Configuration files required to reproduce reported tables

## Not recommended for tracking

- Python bytecode (`__pycache__`, `*.pyc`)
- Large raw logs
- Large generated trajectories
- Temporary debug outputs

## Current scope

The repository contains safety assurance development records around:

- Start-Safe CBF
- Discrete-Time Verification
- Optional V4-C predictive recovery
- Diagnostic efficiency branches

Raw experiment regeneration should use the corresponding scripts and environment notes when available.
