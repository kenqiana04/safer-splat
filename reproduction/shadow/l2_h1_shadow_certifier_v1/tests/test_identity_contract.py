import json
import unittest

from _support import TASK_ROOT
from shadow_contract import CONTRACT_VERSION, NORMATIVE_MODEL, PR93_HEAD


class IdentityContractTests(unittest.TestCase):
    def test_frozen_contract_constants(self):
        self.assertEqual(CONTRACT_VERSION, "L2_H1_SHADOW_CERTIFIER_V1")
        self.assertEqual(NORMATIVE_MODEL, "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1")
        self.assertEqual(PR93_HEAD, "1df09c56eedb53d46f9347695026086319738a89")

    def test_identity_audits_are_passed(self):
        protected = json.loads((TASK_ROOT / "audit/protected_source_audit.json").read_text(encoding="utf-8"))
        symbols = json.loads((TASK_ROOT / "audit/frozen_backend_symbol_map.json").read_text(encoding="utf-8"))
        self.assertEqual(protected["protected_blob_count"], 17)
        self.assertEqual(protected["status"], "PASS_L2_H1_SHADOW_PROTECTED_SOURCE_AUDIT")
        self.assertEqual(symbols["status"], "PASS_FROZEN_BACKEND_SYMBOL_MAP")


if __name__ == "__main__":
    unittest.main()
