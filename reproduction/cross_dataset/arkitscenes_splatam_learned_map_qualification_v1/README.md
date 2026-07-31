# ARKitScenes SplaTAM learned-map qualification V1

This directory records the fail-closed input-identity audit for frozen
ARKitScenes video `48018874`. Raw data, checkpoints, canonical arrays, and
dense logs remain on the 4090 server.

The audit found an internal byte-identity contradiction in the two PR #68 V2
CSV manifests: their committed Git blobs are LF encoded, while their own split
contract records SHA-256 values for CRLF encoded versions.  The CSV records are
semantically equal, but this task requires the declared raw-byte identities.
Accordingly no environment, adapter, smoke, formal mapping, checkpoint,
evaluation, clearance audit, SAFER G0, controller, or variant was run.

`audit_pr68_input_identity.py` is read-only with respect to the source checkout
and writes a machine-readable evidence record to the task-owned output root.
