# No Search After Expiry Policy

`DEADLINE_EXPIRED` is absorbing for the control cycle. Candidate generation, alternative search, backup discovery, backup reconstruction, and terminal search are forbidden. L4 must return `ALT_SEARCH_NOT_ALLOWED` whenever the state is not `DEADLINE_OPEN`.

The Supervisor may arbitrate only among artifacts that were fully certified before expiry and remain identity-valid at commit: an already certified navigation action, an already valid backup witness, or an already certified terminal action. Otherwise it selects the outside-method boundary. Nominal control, desired control, partial witnesses, timed-out certificates, and uncertified candidates are never fallback actions.
