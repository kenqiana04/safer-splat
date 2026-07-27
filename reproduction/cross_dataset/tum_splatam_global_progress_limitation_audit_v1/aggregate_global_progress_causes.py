#!/usr/bin/env python3
import json
from audit_core import global_causes
if __name__ == "__main__": print(json.dumps(global_causes(), indent=2))
