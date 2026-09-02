# Alternative and Backup Role Separation V2

An L3 backup witness and its certified tail are not an alternative source. The executable role is `RETAINED_BACKUP_ACTION`, and its authority is `L3_CERTIFIED_BACKUP_BUNDLE`, not `ALTERNATIVE_SOURCE_AUTHORITY`.

An ordinary alternative must receive fresh C0/L1/L2/L3 evidence. A retained tail action may reuse its immutable bundle certificate only when `BACKUP_TOKEN_STILL_VALID=PASS` and the exact cursor action identity is checked immediately before commit. This narrow reuse does not extend to ordinary alternatives.

A PRIMARY or lawfully sourced ALTERNATIVE may be the source candidate for a new bundle. Non-selected prepared bundles never become fallback-authorized.
