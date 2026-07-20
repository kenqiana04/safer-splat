"""Hashes checkpoint tensors post-run without modifying training semantics."""
from pathlib import Path
import hashlib
def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
