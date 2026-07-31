# Correct ARKitScenes Split V2 Canonical Git Blob Identity V1

This correction changes only text-byte identity handling for the inherited V2
TRAIN and HELDOUT CSV manifests. It establishes Git blob bytes as raw-byte
authority, makes the producer emit LF deterministically, preserves the legacy
CRLF hashes as historical evidence, and forbids every runtime operation.

The corrected branch is based on the immutable PR #69 blocked-evidence commit.
PR #68 and PR #69 remain unchanged. No candidate, V1 joined manifest, group,
frame, field, row order, split label, threshold, seed, DP score, or result
claim is modified.
