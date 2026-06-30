import importlib.util
import unittest
from pathlib import Path

from clickstream_analytics.producer import read_rees46


ROOT = Path(__file__).parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "clickstream.csv"
SPEC = importlib.util.spec_from_file_location(
    "sequential_baseline", ROOT / "jobs" / "sequential_baseline.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SequentialBaselineTests(unittest.TestCase):
    def test_source_time_produces_historical_windows(self) -> None:
        rows = {row["product_id"]: row for row in MODULE.calculate(read_rees46(FIXTURE))}

        self.assertEqual(rows["100"]["observed_5m_windows"], 1)
        self.assertEqual(rows["100"]["avg_trend_score_5m"], 13)
        self.assertEqual(rows["200"]["observed_5m_windows"], 2)
        self.assertEqual(rows["200"]["avg_trend_score_5m"], 2.5)


if __name__ == "__main__":
    unittest.main()
