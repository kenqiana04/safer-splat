# ARKitScenes cross-platform text identity policy V1

## Raw-byte authority

For every tracked text input, the formal raw-byte identity is the SHA-256 of
`git cat-file blob <commit>:<path>`. The Git object ID is recorded separately
and is never described as the file SHA-256.

## Working tree use

A working-tree SHA-256 is only a consistency check. It is authoritative only
after its bytes are proven equal to the commit's Git blob bytes.

## Prohibited identity sources

Do not use a platform-normalized Windows checkout, a PowerShell text pipeline,
a universal-newline decode/re-encode, a temporary JSON/CSV serialization, an
editor save, or any checkout-platform-specific bytes as a formal raw identity.

## Secondary CSV semantic identity

CSV semantic identity is SHA-256 over canonical UTF-8 JSON with one final LF:
`{"fieldnames":[...],"ordered_rows":[...]}`. Fieldname order, row order, and
each parsed field string are preserved; JSON uses `separators=(",", ":")`,
`ensure_ascii=true`, and `sort_keys=false`. It establishes content equality but
never substitutes for the Git-blob raw identity.

## Producer requirements

Tracked CSV must be UTF-8 without BOM, LF-only, and generated through
`csv.DictWriter(..., lineterminator="\n")` with `newline=""`. Text attributes
must explicitly use `eol=lf`. Producers calculate semantic identity after
generation, then freeze the raw SHA only after reading the committed Git blob.
