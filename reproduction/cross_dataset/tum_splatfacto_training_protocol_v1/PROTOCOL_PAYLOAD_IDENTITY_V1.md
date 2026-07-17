# TUM Corrected Protocol Payload Identity V1

## Policy

The immutable execution payload is commit
`de97ad4d071d552dc0cb82127738a1cddd40e4a4`. Evidence-only descendants may
record verification results without changing that payload. Verification must
therefore prove payload ancestry and critical-path immutability, rather than
requiring every later evidence commit to be a new execution payload.

The evidence head before this offline-bundle task is
`f35f38745cd203d7f800e9c76ab67f7e4bec8a97`; the payload is its ancestor.
The comparison found zero changed critical paths.

## Immutable identities

| Item | Git blob SHA | SHA-256 of raw Git blob bytes |
| --- | --- | --- |
| Corrected command | `0d56e187039d5da75f2a147ff1c207bf9ff58efa` | `4a39766b324ffc6c7766a3389589d748bc00925f109ec44fc72e5a705358ec94` |
| Frozen config | `d3e0c104b37304278dd4074787d8781d2281a375` | `0d15d8d6fa84049c6b4c34d6fdcaf77114f569c8d22ea9d010ae8144e6c924ea` |

The training command remains 71 tokens, its argument difference count is zero,
and neither training nor G1 is authorized by this policy.

## Critical-path note

The specified `parameter_provenance.json` is absent in both compared commits.
The tracked provenance artifact is `parameter_provenance.csv`; it is treated as
an additional critical path. The absent JSON path is also protected from
introduction in evidence-only descendants.
