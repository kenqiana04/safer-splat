#!/usr/bin/env python3
from audit_core import map_inventory, navigation_conditioned, reference_authority
if __name__ == "__main__":
    maps=map_inventory(); navigation_conditioned(maps,reference_authority(maps))
