"""Thin task-owned client for the float64 C++ full-mesh oracle backend."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable

import numpy as np


def run_oracle(backend: Path, mesh: Path, queries: Iterable[str], output: Path,
               *, brute_force: bool = False) -> list[list[str]]:
    query_file = output.with_suffix(".queries.txt")
    query_file.parent.mkdir(parents=True, exist_ok=True)
    query_file.write_text("\n".join(queries) + "\n", encoding="utf-8")
    command = [str(backend), str(mesh), str(query_file), str(output)]
    if brute_force:
        command.append("--bruteforce")
    subprocess.run(command, check=True)
    return [line.split() for line in output.read_text(encoding="utf-8").splitlines() if line]


def point_query(point: np.ndarray) -> str:
    return "P " + " ".join(f"{float(x):.17g}" for x in point)


def segment_query(start: np.ndarray, goal: np.ndarray) -> str:
    return "S " + " ".join(f"{float(x):.17g}" for x in np.concatenate((start, goal)))
