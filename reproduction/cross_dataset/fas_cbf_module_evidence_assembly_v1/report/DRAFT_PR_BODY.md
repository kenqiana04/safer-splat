## Scope

PR #81 is preserved at its frozen head. This PR assembles existing compact GT-derived and learned-map evidence only; it performs no new experiment, training, scenario search, controller rollout, tuning, or dataset switch.

## Evidence and claim boundary

- 18 source reports are frozen by commit, Git blob, and SHA-256 in the provenance ledger.
- Map roles remain separated: official SAFER-map module studies, Replica GT-derived Gaussian benchmark, ETH3D learned 3DGS external carrier, and TUM learned-SLAM case study.
- The module matrix preserves active, shadow, diagnostic, negative-ablation, and structural evidence separately.
- DT taxonomy separates endpoint, segment, margin, H-step predicted, executed collision/overlap, and bounded intervention evidence.
- Replica saturation and ETH3D Case D rule out a Full FAS-CBF-versus-SAFER global-superiority claim.

## Paper framing and decision

Frame the work as a modular safety-assurance architecture with configuration-specific module claims. ETH3D shows learned-map viability and an explicit activation limit, not deployment safety.

- FINAL_STATUS: `PASS_MODULE_WISE_EVIDENCE_WITHOUT_FULL_STACK_SUPERIORITY`
- FINAL_DECISION: `FRAME_PAPER_AS_MODULAR_SAFETY_ASSURANCE_NOT_GLOBAL_SUPERIORITY`
- Only next task: `INTEGRATE_FAS_CBF_FULL_FRAMEWORK_WITH_MODULE_SPECIFIC_CLAIMS_V1`
