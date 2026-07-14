# REPORT: Cross-Dataset Raw Asset Acquisition and Integrity Audit

## 1. Purpose
获取并验证原始跨数据集资产；不进行预处理、训练或 SAFER 执行。

## 2. Relationship to Baseline Cross-Dataset G0-G1
本任务只解除原始资产可用性阻断，不构成 GSplat 兼容性或 baseline 泛化证据。

## 3. Fixed Dataset Preregistration
TUM RGB-D `rgbd_dataset_freiburg1_room` 与 Replica Dataset v1 已在下载前固定。

## 4. Official Sources
TUM: `https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_room.tgz`。Replica 元数据来自官方 repository，commit `75fd55679ee189325d3593e838a762dd9163ee57`。

## 5. License and Manual-Approval Boundaries
TUM 许可证已记录为 CC BY 4.0。Replica marker present: `False`；未由本任务创建或伪造。

## 6. Storage and Network Gates
所有原始资产仅位于 `/disk1/zlab/cross_dataset_assets`；自动下载仅允许官方 host，完成后至少保留 50 GiB。Replica 已对 `18` 个官方下载对象执行 HEAD：下载估计 `33899841712` 字节，保守解压估计 `67799683424` 字节，合计空间需求 `101699525136` 字节，存储门槛通过：`True`。

## 7. TUM RGB-D Archive Provenance and Integrity
archive exists: `True`，size: `782381450`，SHA256: `5ace47a1d2e53696bc939a84999293a04a7226958e848a609666691fd3cc38da`。
本次归档来源模式：`user_provided_local_transfer`；本任务直接官网下载：`False`；归档大小与官方 HEAD 一致：`True`。该归档由用户提供的本地文件传输至外部资产目录，未被表述为本任务直接官网下载。

## 8. TUM Archive and File Integrity
gzip/tar and path-traversal gate: `True`；TUM integrity: `True`。

## 9. TUM Timestamp and Association Feasibility
RGB-depth rate: `1.0`；RGB-pose rate: `1.0`；triple rate: `1.0`。这些仅为诊断，不生成 association 文件。

## 10. Replica Official Download Contract
记录官方 metadata、LICENSE 和 `download.sh` hashes；预期分卷为 17 个，连同附加配置共 `18` 个官方对象。完整 Replica v1 仍只能按官方脚本获取。

## 11. Replica Manual License Gate
Replica status: `waiting_for_manual_license_confirmation`。用户人工条款确认是正式下载的前置条件。

## 12. Replica Download and Scene Integrity
未执行 Replica 下载、解压或场景处理；本地现有 Replica 文件和目录未被迁移或用作审计证据。

## 13. External Asset Locations
第三方数据位于 `/disk1/zlab/cross_dataset_assets`，未进入 Git。

## 14. Negative and Neutral Evidence
Replica 等待许可不是数据完整性或 SAFER 方法失败。下载成功也不表示 baseline 能泛化。

## 15. Acquisition Decision
`tum_ready_replica_waiting_manual_license_confirmation`

## 16. Next Processing Entry Conditions
TUM 只有在 `tum_integrity_passed=true` 时可进入单独的预处理任务。Replica 还需用户创建且非空的 acceptance marker。

## 17. Claim Boundaries
This task acquires and verifies raw cross-dataset assets only. It does not preprocess the datasets, train Gaussian maps, or evaluate SAFER baseline generalization.
