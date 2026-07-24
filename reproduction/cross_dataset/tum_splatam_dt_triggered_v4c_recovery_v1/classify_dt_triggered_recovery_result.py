#!/usr/bin/env python3
"""Emit the preregistered final classification."""
import json
from pathlib import Path
print(json.loads(Path(__file__).with_name('validation_result.json').read_text(encoding='utf-8'))['status'])
