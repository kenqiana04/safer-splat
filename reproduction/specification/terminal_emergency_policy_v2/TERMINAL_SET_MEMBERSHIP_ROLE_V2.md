# Terminal Set Membership Role V2

`TERMINAL_SET_MEMBER` is a state predicate and has no action, certificate, eligibility, selection, commit, goal, or emergency authority.

The reusable historical primitive `BRAKING_TO_REST_TERMINAL_SET_V1` tests finite state velocity against its parameterized tolerance. This predicate may be an input to a V2 terminal certificate primitive only behind current geometry, actuator, map, dynamics/timebase, state/time, deadline, and Supervisor authorities.

Membership does not imply goal completion, safe stop, emergency stop, or permission to apply zero control. In particular, a normal navigation initial state can have zero velocity and satisfy membership; timely certified navigation still has higher priority. Therefore `ZERO_VELOCITY_START_DOES_NOT_PREEMPT_NAVIGATION` is mandatory.
