# Formal V2 执行与断点恢复指南

## 1. 最小实现原则

不要重新写 CBF、Active Runtime、oracle 或地图查询逻辑。正式 runner 只负责四件事：

1. 锁定 PR #138 方法源与 map/environment；
2. 按冻结的 100-trial manifest 调用已经验证过的 Pilot V2 单-arm executor；
3. 每次运行写入独立 `attempt_XXX`，成功后只登记到 `FORMAL_ACCEPTED_INDEX.json`，永不覆盖；
4. 发生失败时停在当前 arm。修复 task-local 基础设施后只重跑当前 arm。

正式 runner 本身不做聚合科学分析，因此跑到一半看不到 aggregate progress/collision 对比，避免无意中“边跑边调”。

## 2. 推荐目录

```bash
REPO=/path/to/safer-splat-checkout
CONTROL=/path/to/formal_v2_execution_bundle
RESULT=/disk1/zlab/results/formal_paired_v2
PY=/disk1/zlab/conda_envs/safer_splat_official/bin/python
```

`REPO` 推荐直接 checkout PR #138 head `606edd1c254f4ffaec48e0b84d8f5e5f29c039ec`。如果之后把 protocol 文件作为 protocol-only child commit 放进 repo，也允许，但 runner 会强制检查所有 execution dependency 相对 PR #138 零 diff。

## 3. 第一次启动

最省事：

```bash
chmod +x "$CONTROL/start_formal_v2_tmux.sh"
"$CONTROL/start_formal_v2_tmux.sh" "$REPO" "$CONTROL" "$RESULT"
```

它会依次：
- preflight；
- 在看正式 outcome 前计算并冻结 HARD/MODERATE/EASY；
- 创建 tmux `safer_formal_v2`；
- 开始100 pairs / 200 arms 串行运行。

查看：

```bash
tmux attach -t safer_formal_v2
```

退出但不停止：

```text
Ctrl-b d
```

只看进度（不解盲科学指标）：

```bash
$PY "$CONTROL/run_formal_paired_experiment_v2.py" \
  --checkout "$REPO" \
  --control-dir "$CONTROL" \
  --result-dir "$RESULT" \
  --status
```

## 4. Runner 如何断点恢复

### A. 已接受 arm
`FORMAL_ACCEPTED_INDEX.json` 中存在且 SHA256 一致：

**永不重跑。**

重新执行 `--run` 时自动跳过。

### B. task-local / infrastructure failure
例如：
- `data` / `outputs` symlink；
- 路径；
- launcher；
- environment；
- serializer；
- 磁盘空间；
- 0 scientific cycle 的启动错误。

处理：
1. 保留失败的 `attempt_XXX`；
2. 修基础设施；
3. 重新运行同一个 arm：

```bash
$PY "$CONTROL/run_formal_paired_experiment_v2.py" \
  --checkout "$REPO" \
  --control-dir "$CONTROL" \
  --result-dir "$RESULT" \
  --one --trial 37 --arm ACTIVE_RUNTIME_V2
```

成功后再恢复全批：

```bash
tmux new-session -d -s safer_formal_v2 \
  "$PY '$CONTROL/run_formal_paired_experiment_v2.py' --checkout '$REPO' --control-dir '$CONTROL' --result-dir '$RESULT' --run 2>&1 | tee -a '$RESULT/formal_collection.log'"
```

### C. 合法 scientific outcome
例如 timeout、solver fail、backup、terminal、assurance boundary。

只要：
- execution complete；
- oracle complete；
- evidence/trace/finalization完整；
- `evaluation_eligible=true`；

runner会接受，不需要“修成好看结果”。

### D. core runtime / method / trace integrity failure
例如：
- unauthorized/duplicate plant commit；
- selected/executed mismatch；
- EVIDENCE_INCOMPLETE；
- RECOVERY_REQUIRED；
- 真正 trace cardinality mismatch；
- 新的 core routing defect；
- 必须修改 CBF/L1/L2/L3/Supervisor/transition/geometry/deadline/oracle 才能继续。

**立即停止 Formal V2。**

不要 patch-and-continue。
保存现有 Formal V2 evidence，之后若确需改方法，开 V3/new method version，不能把修前修后数据混在一个 formal result。

## 5. 非正常断电 / SSH 断开

SSH 断开但 tmux 存活：什么都不用做。

机器重启或进程被杀：
- 当前未完成 attempt 保留；
- 已接受 arm 不受影响；
- 重新 `--status`；
- 若 GPU clean，直接再次 `--run`；
- runner 会从第一个 pending arm 接着跑。

不要删除半成品 attempt。

## 6. 正式跑完以后

确认：

```bash
$PY "$CONTROL/run_formal_paired_experiment_v2.py" \
  --checkout "$REPO" --control-dir "$CONTROL" --result-dir "$RESULT" --status
```

应显示：

```text
accepted_arms=200/200
next_pending=NONE
```

然后才运行最终统计：

```bash
$PY "$CONTROL/analyze_formal_paired_experiment_v2.py" \
  --control-dir "$CONTROL" \
  --result-dir "$RESULT" \
  --plots
```

自动输出：
- `FORMAL_ARM_SUMMARY.csv`
- `FORMAL_PAIR_SUMMARY.csv`
- `FORMAL_SAFETY_SUMMARY.json`
- `FORMAL_LIVENESS_SUMMARY.json`
- `FORMAL_RUNTIME_SUMMARY.json`
- `FORMAL_ACTIVE_DIAGNOSTICS.json`
- `FORMAL_INTEGRITY_REGISTER.csv`
- `FORMAL_STATISTICAL_ANALYSIS.json`
- `FORMAL_RAW_EVIDENCE_MANIFEST.json`
- `FORMAL_DIFFICULTY_ANALYSIS.json`
- `REPORT_FORMAL_PAIRED_EXPERIMENT_V2.md`
- 4 张论文分析图

## 7. 最终统计判据

Primary = 85 个 development-light pairs。

### Integrity
85/85 primary pairs eligible。

### Safety
Active：
- collision proxy = 0；
- 0.025 m margin violation = 0；
- Active-only collision discordant pair = 0。

### Progress non-inferiority
`delta = Active progress - Reference progress`

10,000 次 paired bootstrap，seed `20260911`。

PASS：

```text
lower_95%_CI(mean delta) > -0.02
```

### 特别注意
如果 Reference 和 Active 都是 0 collision：
结论是 safety parity / preservation，不是 collision reduction。

## 8. 额度策略

这套执行不需要 Codex陪跑。

Codex只在：
- runner本身存在必须改代码的真实问题；
- core runtime出现新的、无法通过 task-local修复的问题；

才值得使用。

普通运行、断点恢复、统计都直接用终端。
