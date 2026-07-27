#!/usr/bin/env python3
import json
from audit_core import inventory
if __name__ == "__main__": print(json.dumps(inventory(), indent=2))
