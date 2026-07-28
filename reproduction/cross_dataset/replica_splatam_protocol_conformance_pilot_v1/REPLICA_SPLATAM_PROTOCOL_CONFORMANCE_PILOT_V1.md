# Replica SplaTAM Protocol-Conformance Audit and Frozen 60/30 GT-Pose Pilot V1

This task is SplaTAM-only. It freezes `CLOSE_SPLATFACTO_NAVIGATION_MAP_ROUTE` and retains Splatfacto solely as the existing SAFER-native compatibility and negative geometry baseline. It does not alter PR #56 or PR #57.

Frozen inputs are Replica V3 dataset tree `24e21d3bccceb0516ed8b9b49b426964f3954ccd0cd804eedd5846baabd66dcb`, content tree `60a9e0b517ba8e305c4b7ff010bb330c1e38c422c66899398129cce741a06bd0`, PR #56 selection core `1beaacaeb8a4126ff4410aae0b296702a7b84dfaee402e15d90d4f5d70741d19`, and ingestion order `d3dc24d673c97700dc340785425abf8482827c0c81b72a6b33e6972b361c2fb1`.

The permitted scientific execution is exactly one serial 60-frame mapping / 30-frame yaw-plus-60-degree holdout SplaTAM map-only run using GT poses on physical GPU 1, with 120-minute cap and no scientific retry. The runner retains seed 0, official optimization budget, losses, learning rates, densification, pruning, keyframe behavior, frame IDs, and ingestion order. Only task-owned output, log, checkpoint, adapter, and launcher paths differ.

The following remain prohibited: Splatfacto execution, 270-frame training, smoke retraining, official evaluation, Gaussian-SLAM, core changes, hyperparameter changes, scale fitting, Sim3, ICP, tracking, pose optimization, filtering, SAFER navigation, CBF-QP, Start-Safe, Risk-Aware, Recovery/V4-C, and all TUM execution.

Raw checkpoints, arrays, renders, CUDA caches, and full logs are server-only under `/disk1/zlab/maintenance_records/replica_splatam_protocol_conformance_pilot_v1`. This Git directory contains only scripts, compact evidence, figures, protocol, and report.
