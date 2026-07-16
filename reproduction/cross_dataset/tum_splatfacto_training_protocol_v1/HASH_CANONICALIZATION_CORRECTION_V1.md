# TUM Splatfacto Protocol Hash Canonicalization Correction V1

## Root cause and correction

The prior protocol compared a Windows CRLF working-tree hash against a Linux
LF checkout hash. Both `exact_training_command.sh` and
`frozen_training_config.json` are LF Git blobs at
`b56f5eb9af1c67791466f37e1f6c2514958cdcd3`. Their raw Git-blob SHA-256 values
are respectively `22d00fadea7eb1fb43556d4690c78113d317c6d144e96b6ad0d294d27a9369a4`
and `0d15d8d6fa84049c6b4c34d6fdcaf77114f569c8d22ea9d010ae8144e6c924ea`.
CRLF-normalizing those exact blobs yields the prior Windows records
`25e490904204622b0c2014ea4093f52efc507fb0543b675f9fe25871fd0d5b81` and
`52fa5cdb93bcef333fc6e9f1c94043745a535e99d620e1f0fff85850f73f8105`.

Canonical identity is now `git_blob_sha256_v1`: SHA-256 of exact Git blob bytes
at an explicit commit. The directory-local `.gitattributes` contract keeps all
protocol text artifacts LF without changing repository-wide Git configuration.
The command's LF-normalized bytes and the configuration's parsed JSON remain
identical to the base blob.

## Execution boundary

PR #24 remains the immutable blocked-preflight record; its formal attempt count
is zero. This correction neither starts nor authorizes training, evaluation,
rendering, SAFER, navigation, or G1. The expected output directory remains
absent. Server checkout verification is recorded separately before this
correction can be considered ready for a newly authorized execution branch.

## Authoritative server verification

An isolated detached worktree at correction commit
`39d91df9b6527f8683064db524cfe7bdc6aa17e6` verified both working-tree hashes
equal their raw Git-blob canonical hashes, with zero CRLF bytes, LF attributes,
and final newlines. The worktree was clean; the formal output path and
checkpoints remained absent, and no Nerfstudio process was present. GPU compute
processes were observed only and not modified.
