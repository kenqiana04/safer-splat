"""Canonical-field comparison helper; excludes output identity only."""
import json
CANONICAL_FIELDS = ("machine.seed", "pipeline.datamanager.dataparser", "pipeline.model", "max_num_iterations", "load_dir", "load_checkpoint", "load_step")
print(json.dumps({"canonical_fields": CANONICAL_FIELDS, "output_identity_fields_excluded": True}))
