# Terminal Reference Boundary V2

A bundle/token may carry a content-addressed terminal certificate reference, represented terminal state identity, certified zero-hold evidence reference, terminal index, and authority references. These are evidence only.

Tail exhaustion produces supervisor status `EXHAUSTED` and may expose the terminal reference. It does not set `TERMINAL_ACTION_ELIGIBLE`, choose zero-hold, define priority, create an emergency stop, or authorize external supervisor behavior.

`BACKUP_TOKEN_EXHAUSTED != TERMINAL_ACTION_AUTHORIZED`. Terminal and External Emergency Policy remains an independent unresolved blocker.
