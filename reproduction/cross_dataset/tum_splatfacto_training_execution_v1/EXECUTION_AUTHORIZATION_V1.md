# Execution Authorization V1

## User authorization

The user explicitly authorized **Formal TUM Splatfacto Training Execution V1**.
This authorization permits exactly one formal execution of the already frozen
TUM FR1 Room Splatfacto command on the authoritative 4090 server.

## Frozen identity

- Protocol commit: `b56f5eb9af1c67791466f37e1f6c2514958cdcd3`
- Command: `reproduction/cross_dataset/tum_splatfacto_training_protocol_v1/exact_training_command.sh`
- Command SHA-256: `25e490904204622b0c2014ea4093f52efc507fb0543b675f9fe25871fd0d5b81`
- Frozen config SHA-256: `52fa5cdb93bcef333fc6e9f1c94043745a535e99d620e1f0fff85850f73f8105`
- Dataset transforms SHA-256: `b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`
- Expected run: `/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1/splatfacto/20260716_000000`

## One-attempt and monitoring rules

Only one frozen configuration, seed, output path, and formal run are authorized.
After the process starts, activity is monitoring-only. On any failure this task
must preserve the evidence and stop: no resume, retry, altered output path, V2,
parameter change, second seed, or automatic remediation is allowed.

## Post-training boundary

The frozen post-training commands are based on the authoritative Nerfstudio
1.1.5 `ns-eval --help` and `ns-render dataset --help` schemas inspected before
training. They load only the formal run config, evaluate/render the `val` split,
and write under that run's `reports/` and `renders/` subdirectories. They do not
perform pose optimization, similarity alignment, scale fitting, SAFER loading,
ellipsoid querying, navigation, baseline evaluation, or G1 work.

## Permitted success boundary

The maximum successful result is
`PASS_CHECKPOINT_CANDIDATE_READY_FOR_G0_COMPATIBILITY_AUDIT`. It permits only a
later static G0 checkpoint compatibility, metric-geometry, and SAFER
adapter/query audit. It does not authorize G1 or SAFER navigation.
