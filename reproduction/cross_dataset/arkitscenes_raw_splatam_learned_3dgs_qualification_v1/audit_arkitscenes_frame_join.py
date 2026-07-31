#!/usr/bin/env python3
"""Compatibility entrypoint for the frozen ARKitScenes frame-join audit."""
from build_arkitscenes_joined_manifest import main


if __name__ == "__main__":
    raise SystemExit(main())
