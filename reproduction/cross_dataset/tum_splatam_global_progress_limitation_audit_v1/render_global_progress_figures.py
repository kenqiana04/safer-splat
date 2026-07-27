#!/usr/bin/env python3
import json
from audit_core import render_figures
if __name__ == "__main__": print(json.dumps(render_figures(), indent=2))
