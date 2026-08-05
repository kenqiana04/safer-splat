from certifier.result_types import ExecutableStatus
from certifier.state_machine import validate_all_terminal_paths


def test_all_typed_statuses_reachable_and_terminal():
    result=validate_all_terminal_paths()
    assert result["status_count"]==len(ExecutableStatus)
    assert result["all_return_next_cycle"]
