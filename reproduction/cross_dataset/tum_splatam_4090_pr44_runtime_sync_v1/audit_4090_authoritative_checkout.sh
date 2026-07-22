#!/usr/bin/env bash
set -euo pipefail

ROOT=${1:?sync root required}
REPO=/disk1/zlab/projects/safer-splat
mkdir -p "$ROOT/pre_sync" "$ROOT/process_audit"

{
  echo '===== CHECKOUT ====='
  cd "$REPO"
  pwd
  git rev-parse --show-toplevel
  git rev-parse HEAD
  git branch --show-current
  git status --porcelain=v2 --branch --untracked-files=all
  git diff --stat
  git diff --cached --stat
  git remote -v
  git worktree list --porcelain
  git submodule status --recursive || true
  echo '===== LOCKS ====='
  find "$REPO/.git" -name '*.lock' -print
} > "$ROOT/pre_sync/checkout_audit.txt" 2>&1

{
  echo '===== REPOSITORY PROCESSES ====='
  for proc in /proc/[0-9]*; do
    pid=${proc##*/}
    cwd=$(readlink -f "$proc/cwd" 2>/dev/null || true)
    cmd=$(tr '\0' ' ' < "$proc/cmdline" 2>/dev/null || true)
    if [[ "$cwd" == "$REPO"* || "$cmd" == *"$REPO"* ]]; then
      printf 'PID=%s\nCWD=%s\nCMD=%s\n' "$pid" "$cwd" "$cmd"
    fi
  done
  echo '===== GPU ====='
  nvidia-smi || true
  echo '===== TMUX ====='
  tmux ls 2>&1 || true
  echo '===== SCREEN ====='
  screen -ls 2>&1 || true
} > "$ROOT/process_audit/process_audit.txt" 2>&1

cat "$ROOT/pre_sync/checkout_audit.txt"
printf '\n--- PROCESS ---\n'
cat "$ROOT/process_audit/process_audit.txt"
