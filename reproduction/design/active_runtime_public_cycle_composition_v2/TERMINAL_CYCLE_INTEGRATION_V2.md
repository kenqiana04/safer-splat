
# Terminal cycle integration V2

`TerminalRuntime.evaluate(fallback_context, expected_terminal_ref)` is called
only when a Supervisor routing decision admits terminal evaluation. A terminal
result returns to Supervisor for arbitration. Terminal search is not an
emergency shortcut and deadline expiry does not make a terminal automatically
safe. `GOAL_HOLD_RUNTIME_ENABLED=false`; post-hoc goal labels never enter
Supervisor routing.
