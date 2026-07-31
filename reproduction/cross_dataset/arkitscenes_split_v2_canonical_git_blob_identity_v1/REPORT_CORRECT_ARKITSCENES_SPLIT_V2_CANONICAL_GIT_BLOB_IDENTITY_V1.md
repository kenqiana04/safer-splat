# ARKitScenes Split V2 Canonical Git-Blob Identity Correction V1

## Result

`FINAL_STATUS=PASS_ARKITSCENES_SPLIT_V2_CANONICAL_GIT_BLOB_IDENTITY_CORRECTED`

`FINAL_DECISION=FREEZE_CANONICAL_LF_GIT_BLOB_IDENTITIES_AND_RESTART_MAPPING_INPUT_FREEZE`

Only next task: `RESTART_ARKITSCENES_SPLATAM_LEARNED_MAP_QUALIFICATION_FROM_CANONICAL_INPUT_FREEZE_V1`.

## Frozen lineage and fail-closed boundary

- PR #68 remains frozen at `9f068e1708e7422e3e53c01c96fa29242be35f0a` with its original `PASS_ARKITSCENES_SPATIAL_GROUP_SPLIT_V2` result.
- PR #69 remains frozen at `dabaa0bbf44cd81783c3c00d0744f44affaffcb2` with `BLOCKED_BY_ARKITSCENES_MAPPING_INPUT_IDENTITY_MISMATCH`. Its stop was correct: its contract raw SHA values did not match the exact committed blobs. Its tracked root is byte-identical to its frozen commit.
- This correction does not activate an adapter, create an environment, run smoke, mapping, training, checkpointing, export, NVS, clearance, G0, variant, or controller execution.

## Root cause and canonical policy

The independent audit proved an EOL-only mismatch. The original producer wrote platform-dependent CRLF bytes, while the committed Git blobs were LF-only. The producer now explicitly uses `lineterminator="\n"`; the V2 `.gitattributes` pins text CSV/JSON/Markdown/Python to LF. The authority is `SHA-256(git cat-file blob <commit>:<path>)`; Git object IDs are recorded separately and are not file SHA-256 values. CSV semantic hashes are secondary ordered-row identities.

| Manifest | Legacy CRLF SHA-256 | Canonical Git-blob SHA-256 | Git blob OID | Semantic SHA-256 |
|---|---|---|---|---|
| TRAIN | `b2d66720fbb0bc7acc998a81e073a9e4774ece7e3ce2900651ff28bf921c2404` | `167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3` | `a2ddc70775e6d0f9c25f77ef5f869556d83b292c` | `32adca1e09694dce9ff5bebc895109f32f866e1c8ecc845e3927a07f60129d12` |
| HELDOUT | `670255f2e00f04a0e462e1a83cd4c4d0344e92906604aba9312aa7baabb3b78e` | `7b65f741e901690f2a723579d75200eebe7b9e77b0cd57c030d4a14d0474c0c7` | `cf28dd385711a31733360e5fc21dce229ce605bc` | `69c8328511cd8405b17b2fc17da9f557ed69ac75b3cfc442f380d586ecab7117` |

The legacy CRLF hashes are retained in the V2 contract as `PRECOMMIT_PLATFORM_DEPENDENT_NOT_AUTHORITATIVE`. The old/new split identities are `54f8c9e68ab0e1129be776fc6e911e6ee2011d75123626227ce7cbaa2a660204` → `0e0d8132aee942d4fc9c231ca3369851694042abe5878482664a0ff184702625` with reason `EOL_CANONICALIZATION_ONLY`; semantic change count is 0.

## Verification

- EOL-only proof: `PASS_EOL_ONLY_MANIFEST_MISMATCH`; deterministic LF→CRLF reproduces both legacy declared hashes, with no non-EOL byte difference.
- Fresh producer regeneration: `PASS_FRESH_LF_REGENERATION` across three clean processes; all LF-only and identical raw/tree identities.
- Semantic regression: `PASS_SEMANTIC_NO_CHANGE`; fieldnames and every ordered row are unchanged.
- Split regression: `PASS_SPLIT_INVARIANT_REGRESSION`; TRAIN/HELDOUT = 214/53, groups = 8/5, selected group tuple = `8ad320980bb36edb2accb38629ec3046095c9ef7735fbb748f4e112ee75bd388`, overlap/cross-edge/discard/duplicate = 0, and the V2 DP score is unchanged.
- Dependency graph: `PASS_IDENTITY_DEPENDENCY_GRAPH`. Six raw-identity derived V2 records were updated/reviewed; group/selection identities remain frozen.
- Post-commit Git object validation: Windows `PASS_CANONICAL_GIT_BLOB_IDENTITY`, Linux `PASS_CANONICAL_GIT_BLOB_IDENTITY`.
- Cross-platform checkout validation: Windows and isolated Linux both equal their exact Git blobs; `PASS_CROSS_PLATFORM_CHECKOUT_IDENTITY`.
- Server V2 validator: `V2_SPLIT_VALIDATION_PASS` from `/disk1/zlab/maintenance_records/arkitscenes_split_v2_canonical_git_blob_identity_v1/server_v2_validation_result_bf4483af.json`.

## Runtime boundary

All prohibited runtime counters are zero: `{"checkpoint": 0, "clearance": 0, "controller": 0, "gaussian_export": 0, "map": 0, "new_arkitscenes_downloads": 0, "nvs": 0, "safer_g0": 0, "smoke": 0, "splatam_environment_creation": 0, "training": 0, "variant_training": 0}`. Final read-only GPU 1 observation was `1, 6 MiB, 0 %`; other SSH sessions were preserved. No learned map result exists.
