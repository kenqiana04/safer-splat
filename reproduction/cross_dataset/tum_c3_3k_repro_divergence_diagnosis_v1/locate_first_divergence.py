"""Read the committed classification rather than perform a fourth replay."""
from pathlib import Path
print(Path(__file__).with_name("first_divergence_summary.json").read_text(encoding="utf-8"))
