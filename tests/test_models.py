import unittest
from datetime import timezone

from clickstream_analytics.models import ClickEvent


class ModelTests(unittest.TestCase):
    def test_rees46_adapter_normalises_event(self) -> None:
        event = ClickEvent.from_rees46(
            {
                "event_time": "2019-10-01 00:00:00 UTC",
                "event_type": "cart",
                "product_id": "42",
                "category_id": "7",
                "category_code": "electronics.phone",
                "brand": "test",
                "price": "12.50",
                "user_id": "user-1",
                "user_session": "session-1",
            }
        )

        self.assertEqual(event.event_type, "cart")
        self.assertEqual(event.event_time.tzinfo, timezone.utc)
        self.assertEqual(event.price, 12.5)
        self.assertEqual(ClickEvent.from_dict(event.to_dict()), event)

    def test_event_rejects_unknown_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported event type"):
            ClickEvent.from_rees46(
                {
                    "event_time": "2019-10-01 00:00:00 UTC",
                    "event_type": "checkout",
                    "product_id": "42",
                    "user_id": "user-1",
                    "user_session": "session-1",
                }
            )


if __name__ == "__main__":
    unittest.main()
