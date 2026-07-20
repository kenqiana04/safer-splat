"""Documentation-only immutable PR33 launcher entry point.

The executed server copies are Git-object snapshots under DIAG_ROOT/tmp/pr33_exact.
"""
from pathlib import Path
PR33 = "fe78814ca0b9e7c840aa99214fa6cd41e4021c5e"
assert PR33 and Path(__file__)
