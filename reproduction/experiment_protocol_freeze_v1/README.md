# Experiment Protocol Freeze V1

This directory is the sole change surface for the protocol freeze rooted at `41ccb54d2e9f10c0b3b559431a58a5763977d462`.

Run from the repository root:

```powershell
python reproduction/experiment_protocol_freeze_v1/scripts/collect_freeze_provenance.py
python reproduction/experiment_protocol_freeze_v1/scripts/build_trial_manifests.py
python reproduction/experiment_protocol_freeze_v1/scripts/write_commit_lock.py
python reproduction/experiment_protocol_freeze_v1/scripts/build_freeze_bundle.py
python reproduction/experiment_protocol_freeze_v1/scripts/validate_freeze_bundle.py
```

The validator performs no experiment and must be re-run after any frozen artifact changes. Re-run `build_freeze_bundle.py` immediately before validation so the manifest excludes only itself and matches all other files.
