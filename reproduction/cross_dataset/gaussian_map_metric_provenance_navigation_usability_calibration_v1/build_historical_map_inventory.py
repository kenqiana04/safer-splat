#!/usr/bin/env python3
from audit_core import availability, map_inventory, reference_authority
if __name__ == "__main__":
    maps=map_inventory(); availability(maps); reference_authority(maps)
