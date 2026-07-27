"""Identity-only entry point for the direct-safe gate."""

from gate_core import ensure_root, identity


if __name__ == "__main__":
    ensure_root()
    print(identity()["status"])
