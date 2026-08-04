#!/usr/bin/env python3
"""Read-only inventory of Python modules available to the offline asset audit."""

import importlib.util
import json
import platform


MODULES = ["numpy", "scipy", "PIL", "trimesh", "matplotlib", "open3d"]


def main() -> None:
    print(json.dumps({
        "python": platform.python_version(),
        "modules": {name: importlib.util.find_spec(name) is not None for name in MODULES},
    }, sort_keys=True))


if __name__ == "__main__":
    main()
