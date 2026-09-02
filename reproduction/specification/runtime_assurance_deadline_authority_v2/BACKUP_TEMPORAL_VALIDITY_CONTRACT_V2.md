# Backup Temporal Validity Contract V2

`VALID_BACKUP` exists only when certification completed before expiry and the witness binds all of:

- geometry authority and content identity;
- actuator authority and admissible selected-control identity;
- the current state snapshot identity;
- map authority and immutable map identity;
- an explicit temporal-validity token/window.

A partial backup, a witness completed after expiry, or a witness with any identity mismatch is not valid. On warning, a previously started bounded certification may finish only before the absolute deadline. After expiry the Supervisor may select an already valid witness, but no module may reconstruct, extend, recertify, or discover one.
