from datetime import timedelta
from pathlib import Path
import unittest

from clickstream_analytics.producer import read_rees46
from clickstream_analytics.speed import SlidingWindowAnalytics


FIXTURE = Path(__file__).parent / "fixtures" / "clickstream.csv"


class SpeedTests(unittest.TestCase):
    def test_sliding_window_ranking_and_funnel(self) -> None:
        analytics = SlidingWindowAnalytics(window=timedelta(minutes=5))
        events = list(read_rees46(FIXTURE))
        for event in events[:7]:
            analytics.process(event)

        snapshot = analytics.snapshot()
        self.assertEqual(snapshot["events_in_window"], 5)
        self.assertEqual(
            snapshot["top_products"][0],
            {
                "product_id": "100",
                "trend_score": 9,
                "views": 1,
                "carts": 1,
                "purchases": 1,
            },
        )
        self.assertEqual(snapshot["funnel"]["view_sessions"], 2)
        self.assertEqual(snapshot["funnel"]["cart_sessions"], 2)
        self.assertEqual(snapshot["funnel"]["purchase_sessions"], 1)
        self.assertEqual(snapshot["funnel"]["cart_to_purchase_dropoff"], 0.5)

    def test_abandonment_requires_timeout_without_purchase(self) -> None:
        analytics = SlidingWindowAnalytics(abandonment_timeout=timedelta(minutes=15))
        events = list(read_rees46(FIXTURE))
        for event in events:
            analytics.process(event)

        snapshot = analytics.snapshot()
        signalled_sessions = {
            item["session_id"] for item in snapshot["latest_abandoned_carts"]
        }
        self.assertIn("s1", signalled_sessions)
        self.assertNotIn("s2", signalled_sessions)
        self.assertNotIn("s3", signalled_sessions)


if __name__ == "__main__":
    unittest.main()
