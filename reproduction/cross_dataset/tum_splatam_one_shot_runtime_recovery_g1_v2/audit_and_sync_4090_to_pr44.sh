#!/usr/bin/env bash
set -euo pipefail
ROOT=${1:?root}
REPO=/disk1/zlab/projects/safer-splat
TARGET=f63b4c496861c4f8881348d74244c1ff9a528d51
BRANCH=safer-world-frame-stable-ellipsoid-hessian-runtime-correction-v1
mkdir -p "$ROOT/pre_sync" "$ROOT/process_audit" "$ROOT/sync" "$ROOT/post_sync"
cd "$REPO"
status=$(git status --porcelain=v2 --untracked-files=all)
printf '%s\n' "$status" > "$ROOT/pre_sync/status_before.txt"
if [[ -n "$status" ]]; then echo BLOCKED_BY_4090_AUTHORITATIVE_CHECKOUT_DIRTY; exit 20; fi
locks=$(find "$REPO/.git" -name '*.lock' -print)
printf '%s\n' "$locks" > "$ROOT/process_audit/git_locks.txt"
if [[ -n "$locks" ]]; then echo BLOCKED_BY_4090_AUTHORITATIVE_CHECKOUT_ACTIVE; exit 21; fi
active=0
for proc in /proc/[0-9]*; do
  p=${proc##*/}; [[ "$p" = "$$" ]] && continue
  cwd=$(readlink -f "$proc/cwd" 2>/dev/null || true)
  cmd=$(tr '\0' ' ' < "$proc/cmdline" 2>/dev/null || true)
  if [[ "$cwd" == "$REPO"* || "$cmd" == *"$REPO"* ]]; then
    printf 'PID=%s CWD=%s CMD=%s\n' "$p" "$cwd" "$cmd" >> "$ROOT/process_audit/active_repo_processes.txt"
    active=$((active+1))
  fi
done
if [[ "$active" -ne 0 ]]; then echo BLOCKED_BY_4090_AUTHORITATIVE_CHECKOUT_ACTIVE; exit 22; fi
pre=$(git rev-parse HEAD)
short=${pre:0:8}
rb="maintenance/4090-pre-pr44-g1-v2-$short"
if git show-ref --verify --quiet "refs/heads/$rb"; then rb="$rb-$(date -u +%Y%m%dT%H%M%SZ)"; fi
git branch "$rb" "$pre"
git rev-parse "$rb" > "$ROOT/sync/rollback_branch_head.txt"
printf '%s\n' "$rb" > "$ROOT/sync/rollback_branch.txt"
git fetch --prune origin "$BRANCH"
remote=$(git rev-parse "origin/$BRANCH")
printf '%s\n' "$remote" > "$ROOT/sync/remote_head.txt"
[[ "$remote" = "$TARGET" ]] || { echo BLOCKED_BY_PR44_REMOTE_HEAD_MISMATCH; exit 23; }
for pair in "splat/distances.py d7f17b67df40e36e458c7a5ed77c4a04659c6f35" "splat/gsplat_utils.py 782c38eca50e78c605085b481155ed61e4607336" "cbf/cbf_utils.py 7c6e1300b125cc0a2a950ac2835a1fbe3d0de113" "reproduction/cross_dataset/safer_world_frame_stable_ellipsoid_hessian_runtime_correction_v1/SAFER_ELLIPSOID_QUERY_NUMERICAL_CONTRACT_V2.json 7a0d85b0b334c2e94ccc23b033d8453322d72fe1"; do
  set -- $pair
  got=$(git rev-parse "$TARGET:$1")
  printf '%s %s\n' "$1" "$got" >> "$ROOT/sync/target_blobs.txt"
  [[ "$got" = "$2" ]] || { echo BLOCKED_BY_PR44_TARGET_BLOB_MISMATCH; exit 24; }
done
git switch --detach "$TARGET"
git rev-parse HEAD > "$ROOT/post_sync/head.txt"
git status --porcelain=v2 --branch --untracked-files=all > "$ROOT/post_sync/status.txt"
[[ "$(git rev-parse HEAD)" = "$TARGET" ]] && [[ ! -s "$ROOT/post_sync/status.txt" ]] || { echo BLOCKED_BY_POST_SYNC_RUNTIME_IDENTITY_MISMATCH; exit 25; }
echo PASS_SYNC
