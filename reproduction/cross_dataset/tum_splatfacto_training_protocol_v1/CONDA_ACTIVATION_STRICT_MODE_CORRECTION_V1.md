# Conda Activation Strict-Mode Correction V1

V1R3 (PR #27) remained attempt 0 because `ns-train` never appeared: the frozen
script enabled `set -u` before `conda activate`, and a compiler deactivate hook
read an unset variable. The V1R3 recorded hook/variable were
`deactivate-gfortran_linux-64.sh` and `GFORTRAN`.

An isolated server before-probe reproduced the same Conda-deactivate nounset
failure class with `deactivate-gcc_linux-64.sh` and
`_CONDA_PYTHON_SYSCONFIGDATA_NAME_USED`. The correction therefore changes only
the shell order: `set -eo pipefail`, source Conda, activate
`safer_splat_official`, then `set -u`.

No `GFORTRAN` patch, Conda hook change, environment change, training argument
change, training, output directory, checkpoint, evaluation, render, SAFER, or
G1 operation is included. The frozen configuration remains byte-identical and
the `ns-train` token list is unchanged.
