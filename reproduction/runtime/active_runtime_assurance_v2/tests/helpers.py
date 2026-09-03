from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    CertificateStatus,
    EvidenceResult,
    RuntimeStateSnapshot,
)


def snapshot(cycle: int = 0) -> RuntimeStateSnapshot:
    return RuntimeStateSnapshot.create(
        trial_id="trial-1",
        cycle_index=cycle,
        state=(0.0, 0.0, 0.0, 0.1, -0.1, 0.0),
        goal=(1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        map_identity="map:g3:abc",
        dt=0.05,
    )


def pass_backend(*args, **kwargs) -> EvidenceResult:
    return EvidenceResult(CertificateStatus.PASS, "CERTIFIED", "evidence:pass")


def fail_backend(*args, **kwargs) -> EvidenceResult:
    return EvidenceResult(CertificateStatus.FAIL, "FINITE_UNSAFE", "evidence:fail")
