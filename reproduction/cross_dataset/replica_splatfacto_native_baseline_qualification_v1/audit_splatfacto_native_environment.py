#!/usr/bin/env python3
"""Read-only package and CUDA audit for the existing native environment."""
from __future__ import annotations

from _common import PYTHON, ROOT, SPLATNAV_REPO, atomic_json, capture, ensure_dirs


def main():
    ensure_dirs()
    code = "import sys,torch,nerfstudio,gsplat,importlib.metadata as m\nprint(sys.version)\nprint(torch.__version__)\nprint(torch.version.cuda)\nprint(m.version('nerfstudio'))\nprint(getattr(gsplat,'__version__','unknown'))\nprint(nerfstudio.__file__)\nprint(gsplat.__file__)"
    probe = capture([str(PYTHON), "-B", "-c", code], cwd=SPLATNAV_REPO, timeout=120)
    status = "SPLATFACTO_NATIVE_ENVIRONMENT_READY" if probe["returncode"] == 0 else "BLOCKED_BY_SPLATFACTO_NATIVE_ASSET_OR_ENVIRONMENT_UNAVAILABLE"
    out = {"status": status, "environment_python": str(PYTHON), "repository": str(SPLATNAV_REPO), "probe": probe, "required_native_packages": ["nerfstudio", "gsplat", "torch"], "online_upgrade": False, "environment_modified": False}
    atomic_json(ROOT / "environment_audit" / "splatfacto_native_environment_audit.json", out)
    print(status)


if __name__ == "__main__":
    main()
