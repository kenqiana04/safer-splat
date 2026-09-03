import unittest

from reproduction.runtime.active_runtime_assurance_v2.alternative_provider import NativeExistingAlternativeProvider
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot


class AlternativeProviderTests(unittest.TestCase):
    def test_empty_inventory_is_legal(self):
        result = NativeExistingAlternativeProvider().enumerate(snapshot())
        self.assertEqual(result.status, "NO_ALTERNATIVE_AVAILABLE")
        self.assertEqual(result.candidates, ())


if __name__ == "__main__": unittest.main()
