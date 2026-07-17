# Content-Addressed Payload Verification Policy V1

The authoritative execution identity is immutable commit `de97ad4`, protocol
path, Git blob identities, and hashes of raw blob bytes. Complete ancestor
history is not necessary to validate the extracted execution payload. `git
archive` reads the named commit's objects directly; the server must independently
verify package SHA-256, every file's SHA-256, Git blob SHA, size, mode, and
critical-file presence. Any mismatch blocks verification. This policy preserves
all data, environment, GPU, retry, and training constraints and never authorizes
training. Historical transport, shallow-history, and mirror-fetch blocks are
infrastructure failures, not evidence that the payload is damaged.
