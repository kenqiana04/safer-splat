# ETH3D Delivery Area Frozen Assets Contract Audit V1

This continuation is rooted at PR #77 head
`aea42e4ec9baea5b7d4843b155b02c74a242a56b` and is restricted to the nine
frozen official ETH3D archives and the asset/split/reference/UNKNOWN/route
contract audit described by the authorization.

The pre-download gate requires at least 40 GB decimal free under `/disk1/zlab`
and an existing `7z` or `7zz` executable. Installation or substitution of the
archive runtime is not authorized. On 2026-08-04 the disk gate passed, but no
`7z`, `7zz`, or `7za` executable existed in PATH, standard system locations,
the existing Conda roots, user-local roots, or `/opt`; `p7zip-full` was reported
as not installed. The task therefore stopped before HEAD revalidation or any
payload transfer with:

`FINAL_STATUS=BLOCKED_BY_7Z_RUNTIME_UNAVAILABLE`

No environment, training, map, controller, candidate-map, split, reference,
UNKNOWN, route, or evaluator execution was attempted. `training_authorized`
remains `false`.
