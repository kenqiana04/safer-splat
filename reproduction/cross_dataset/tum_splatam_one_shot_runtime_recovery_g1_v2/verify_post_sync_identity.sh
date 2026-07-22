#!/usr/bin/env bash
set -euo pipefail
ROOT=${1:?root}; REPO=/disk1/zlab/projects/safer-splat; TARGET=f63b4c496861c4f8881348d74244c1ff9a528d51
cd "$REPO"; mkdir -p "$ROOT/post_sync"
head=$(git rev-parse HEAD); status=$(git status --porcelain=v2 --untracked-files=all)
printf '%s\n' "$head" > "$ROOT/post_sync/head_verified.txt"; printf '%s\n' "$status" > "$ROOT/post_sync/status_verified.txt"
[[ "$head" = "$TARGET" && -z "$status" ]] || { echo BLOCKED_BY_POST_SYNC_RUNTIME_IDENTITY_MISMATCH; exit 1; }
for pair in "splat/distances.py d7f17b67df40e36e458c7a5ed77c4a04659c6f35" "splat/gsplat_utils.py 782c38eca50e78c605085b481155ed61e4607336" "cbf/cbf_utils.py 7c6e1300b125cc0a2a950ac2835a1fbe3d0de113" "reproduction/cross_dataset/safer_world_frame_stable_ellipsoid_hessian_runtime_correction_v1/SAFER_ELLIPSOID_QUERY_NUMERICAL_CONTRACT_V2.json 7a0d85b0b334c2e94ccc23b033d8453322d72fe1"; do set -- $pair; got=$(git rev-parse "HEAD:$1"); printf '%s %s\n' "$1" "$got" >> "$ROOT/post_sync/current_blobs.txt"; [[ "$got" = "$2" ]] || exit 2; done
sha256sum splat/distances.py splat/gsplat_utils.py cbf/cbf_utils.py reproduction/cross_dataset/safer_world_frame_stable_ellipsoid_hessian_runtime_correction_v1/SAFER_ELLIPSOID_QUERY_NUMERICAL_CONTRACT_V2.json > "$ROOT/post_sync/current_sha256.txt"
echo PASS_POST_SYNC
