#!/usr/bin/env python3
import json
from audit_core import attribution_and_oscillation
if __name__ == "__main__": print(json.dumps(attribution_and_oscillation()[0], indent=2))
