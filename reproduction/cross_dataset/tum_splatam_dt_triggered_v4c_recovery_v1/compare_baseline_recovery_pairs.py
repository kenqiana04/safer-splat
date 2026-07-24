#!/usr/bin/env python3
"""Compact comparison artifact is frozen in paired_comparison_summary.json."""
from pathlib import Path
print(Path(__file__).with_name('paired_comparison_summary.json').read_text(encoding='utf-8'))
