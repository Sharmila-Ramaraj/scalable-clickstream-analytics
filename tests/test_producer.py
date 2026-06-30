import io
import json
import unittest
from pathlib import Path

from clickstream_analytics.producer import JsonLinesSink, read_rees46, replay


FIXTURE = Path(__file__).parent / "fixtures" / "clickstream.csv"


class ProducerTests(unittest.TestCase):
    def test_replay_rebases_time_and_preserves_source(self) -> None:
        output = io.StringIO()
        count = replay(
            read_rees46(FIXTURE, limit=3),
            JsonLinesSink(output),
            events_per_second=2,
            sleep=False,
        )
        rows = [json.loads(line) for line in output.getvalue().splitlines()]

        self.assertEqual(count, 3)
        self.assertTrue(rows[0]["source_event_time"].startswith("2019-10-01"))
        self.assertNotEqual(rows[0]["event_time"], rows[0]["source_event_time"])
        self.assertEqual(rows[0]["session_id"], "s1")
        self.assertGreater(rows[2]["event_time"], rows[1]["event_time"])


if __name__ == "__main__":
    unittest.main()
