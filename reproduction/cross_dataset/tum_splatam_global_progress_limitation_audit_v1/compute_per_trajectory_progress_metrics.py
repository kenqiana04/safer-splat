#!/usr/bin/env python3
import json
from audit_core import per_trajectory_metrics
if __name__ == "__main__": print(json.dumps(per_trajectory_metrics(), indent=2))
