# Gaussian-SLAM Resolution Adaptation Contract Audit V1

This task is a source-and-input contract audit only. It freezes the Replica V3 identities, recovers the historical PR #56 exception, reads the official frozen Gaussian-SLAM archive, and enumerates candidate populations for the frozen 16-frame smoke and 60-frame pilot inputs.

It explicitly prohibits Gaussian-SLAM mapping, optimizer steps, checkpoints, Gaussian maps, holdout rendering, geometry metrics, official evaluation, Splatfacto/SplaTAM reruns, SAFER/navigation, and TUM.

The final evidence package records whether the frozen source uniquely derives a non-core resolution adaptation. If it does not, the task creates explicit `NOT_CREATED_DUE_TO_NO_LEGAL_ADAPTATION` artifacts instead of inventing a count, a clamp, or a scaling rule.
