#!/usr/bin/env python3
import json
from audit_core import stall_onset
if __name__ == "__main__": print(json.dumps(stall_onset(), indent=2))
