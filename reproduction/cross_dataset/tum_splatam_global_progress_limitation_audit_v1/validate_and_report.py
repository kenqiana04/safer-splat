#!/usr/bin/env python3
import json
from audit_core import validate_and_report
if __name__ == "__main__": print(json.dumps(validate_and_report(), indent=2))
