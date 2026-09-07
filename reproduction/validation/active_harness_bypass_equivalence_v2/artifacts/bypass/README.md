# BYPASS failure evidence

No BYPASS arm finalized a JSONL trace or `TrialTraceLock`. The pre-correction arm was rejected by actuator admission before commit. The post-correction arm committed the first plant transition, then trace append raised `TRIAL_IDENTITY_MISMATCH`. Both stderr files and directories remain on the authority server with hashes in `SERVER_EVIDENCE_MANIFEST.json`.
