import unittest

from clickstream_analytics.serving import merge_views


class ServingTests(unittest.TestCase):
    def test_merge_flags_activity_at_twice_baseline(self) -> None:
        speed = {
            "as_of": "2026-07-31T12:00:00+00:00",
            "top_products": [
                {
                    "product_id": "100",
                    "trend_score": 20,
                    "views": 10,
                    "carts": 0,
                    "purchases": 2,
                }
            ],
            "funnel": {"cart_to_purchase_dropoff": 0.5},
            "events_in_window": 12,
            "processed_events_total": 100,
        }
        baseline = [
            {
                "product_id": "100",
                "avg_views_5m": 5,
                "avg_carts_5m": 0,
                "avg_purchases_5m": 1,
                "avg_trend_score_5m": 10,
            }
        ]

        result = merge_views(speed, baseline)
        product = result["trending_products"][0]
        self.assertEqual(product["activity_lift"], 2.0)
        self.assertTrue(product["is_unusually_trending"])


if __name__ == "__main__":
    unittest.main()
