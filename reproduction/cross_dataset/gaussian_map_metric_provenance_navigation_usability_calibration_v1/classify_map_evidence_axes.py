#!/usr/bin/env python3
from audit_core import availability, evidence_profiles, map_inventory
if __name__ == "__main__":
    maps=map_inventory(); evidence_profiles(maps,availability(maps))
