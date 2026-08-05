from certifier.result_types import ExecutableStatus
from certifier.state_machine import trace_for_status


def test_infrastructure_not_scientific_failure():
    trace=trace_for_status(ExecutableStatus.INFRASTRUCTURE_FAILURE)
    assert "INFRA_FAILURE" in trace
    assert "BACKUP_NOT_FOUND" not in trace
