#!/usr/bin/env python3
import json
from audit_core import normalize
if __name__ == "__main__": print(json.dumps(normalize(), indent=2))
