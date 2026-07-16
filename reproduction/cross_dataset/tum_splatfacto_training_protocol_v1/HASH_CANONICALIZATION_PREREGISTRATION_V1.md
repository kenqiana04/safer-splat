# TUM Splatfacto Protocol Hash Canonicalization Preregistration V1

## 1. Observed issue

The Formal TUM Splatfacto Training Protocol V1 recorded Windows-side hashes
while the authorized Linux checkout observed different hashes:

| Artifact | Recorded Windows hash | Observed Linux hash |
| --- | --- | --- |
| `exact_training_command.sh` | `25e490904204622b0c2014ea4093f52efc507fb0543b675f9fe25871fd0d5b81` | `22d00fadea7eb1fb43556d4690c78113d317c6d144e96b6ad0d294d27a9369a4` |
| `frozen_training_config.json` | `52fa5cdb93bcef333fc6e9f1c94043745a535e99d620e1f0fff85850f73f8105` | `0d15d8d6fa84049c6b4c34d6fdcaf77114f569c8d22ea9d010ae8144e6c924ea` |

The formal execution was blocked before `tmux` or `ns-train`; the formal
attempt count remains zero. PR #24 is retained as that immutable blocked
preflight record.

## 2. Primary hypothesis

The command discrepancy is hypothesized to be an otherwise-identical CRLF vs
LF byte representation. The configuration discrepancy may have the same cause,
but it must be independently verified rather than assumed.

## 3. Canonical hash policy

The authoritative hash of every text protocol artifact is the SHA-256 of the
exact Git blob bytes at an explicitly recorded protocol commit. Windows working
tree bytes, editor-save bytes, PowerShell text-pipeline bytes, JSON
parse/reserialize output, and temporary line-ending conversions are not
authoritative protocol hashes.

## 4. Git blob retrieval rule

Resolve the object with `git rev-parse <commit>:<path>`, then retrieve exactly
those bytes using `git cat-file blob <blob_sha>`. Calculate SHA-256 directly on
the returned byte stream.

## 5. Semantic immutability rule

This correction may change only EOL policy, hash provenance, recorded expected
hashes, validator logic, bundle metadata, and reports. It must not change the
training-command or frozen-configuration semantics.

## 6. Execution boundary

This correction does not authorize training. Any future formal execution
requires separate user authorization, a new execution branch and Draft PR, and
must not reuse the blocked PR #24 branch. G1 remains forbidden.
