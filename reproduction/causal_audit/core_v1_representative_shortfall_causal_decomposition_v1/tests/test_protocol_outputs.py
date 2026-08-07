from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProtocolOutputTests(unittest.TestCase):
    def test_protocol_factor_directories_and_named_figures_exist(self) -> None:
        for number in range(1, 12):
            self.assertTrue(list(ROOT.glob(f"factor_f{number:02d}_*")))
        figures = ROOT / "figures"
        self.assertEqual(len(list(figures.glob("*.png"))), 28)
        self.assertTrue((ROOT / "causal_attribution/final_factor_verdicts.json").is_file())
        self.assertTrue((ROOT / "decision/final_causal_decomposition_decision.json").is_file())
