"""Regenerate compact report and figures from existing task-owned artifacts."""

from navigation_audit_core import rerender_existing


if __name__ == "__main__":
    print(rerender_existing()["status"])
