# Backup and Terminal Actuator Compatibility

The V2 target contract has exactly one normative actuator-admission authority for nominal, alternative, backup, and terminal controls.

The existing reusable V1 components support this structure: `BackupCertifier` checks the initial candidate and each braking command with `self.dynamics.bounds`; `DeterministicBrakingPolicy` derives controls and stopping horizon from those same bounds; `TerminalCertifier` uses the zero control for both the current-point check and zero-hold segment.

V2 reuse is conditional. The shared bounds must be injected from `NORMATIVE_COMPONENTWISE_ACCELERATION_AUTHORITY_V2`; no constructor or layer may load independent literals. Every backup control receives a unique identity and actuator certificate. Terminal zero uses one stable identity and the same bounds.

Rate, delay, quantization, tracking error, and physical hardware limits are not established. Backup/terminal certificates may be interpreted only under the normative benchmark model, not as hardware execution guarantees.

Verdict: `PASS_BACKUP_TERMINAL_SINGLE_ACTUATOR_CONTRACT_V2_DESIGN`.
