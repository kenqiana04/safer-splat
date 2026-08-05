from certifier.result_types import ExecutableStatus
from certifier.state_machine import trace_for_status


def test_terminal_action_returns_next_cycle():
    trace=trace_for_status(ExecutableStatus.CERTIFIED_TERMINAL_ACTION)
    assert "ZERO_CONTROL_HOLD" in trace and trace[-1]=="NEXT_CYCLE_DIAGNOSIS"
