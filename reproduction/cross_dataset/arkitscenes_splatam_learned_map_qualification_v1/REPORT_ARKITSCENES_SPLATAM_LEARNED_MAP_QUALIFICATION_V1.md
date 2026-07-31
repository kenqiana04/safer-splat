# ARKitScenes SplaTAM learned-map qualification V1

## Result

`BLOCKED_BY_ARKITSCENES_MAPPING_INPUT_IDENTITY_MISMATCH`

The task stopped at the mandatory PR #68 raw-byte input freeze. No environment,
dataset adapter, smoke, baseline, checkpoint, export, held-out evaluation,
clearance audit, SAFER G0, confidence variant, controller, or hyperparameter
sweep was run.

## Evidence

The frozen PR #68 head is `9f068e1708e7422e3e53c01c96fa29242be35f0a`.
Its split contract declares these raw SHA-256 values:

| Manifest | Declared SHA-256 | Git blob SHA-256 | Result |
| --- | --- | --- | --- |
| TRAIN (214 rows) | `b2d66720fbb0bc7acc998a81e073a9e4774ece7e3ce2900651ff28bf921c2404` | `167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3` | mismatch |
| HELDOUT (53 rows) | `670255f2e00f04a0e462e1a83cd4c4d0344e92906604aba9312aa7baabb3b78e` | `7b65f741e901690f2a723579d75200eebe7b9e77b0cd57c030d4a14d0474c0c7` | mismatch |

The working-tree files equal their Git blobs. Both blobs use LF only; the
declared values reproduce only when the split writer emits CRLF. The CSV records
are semantically equal after universal-newline parsing, but the frozen task
requires byte-exact manifest identities and does not authorize rewriting PR #68
or normalizing its inputs.

## Completed read-only work

- Verified the proxy wrapper, loopback-only server proxy, frozen SplaTAM
  checkout/submodule, GPU 1 idle state, and disk capacity.
- Audited the official `scripts/gaussian_splatting.py` semantics before runtime.
- Preserved PR #68 unchanged and did not modify the watchdog, SSH, network,
  firewall, raw data, or official SplaTAM checkout.

## Decision boundary

No learned map is selected and no downstream navigation handoff exists. The
only valid next step is a separately authorized correction that makes PR #68's
committed manifest bytes and declared raw-byte identities agree; the present
task must then restart from its input freeze.
