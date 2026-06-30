"""Stateful sliding-window analytics for the speed layer."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

from .models import ClickEvent


@dataclass(frozen=True, slots=True)
class AbandonmentSignal:
    session_id: str
    product_id: str
    cart_time: datetime
    detected_at: datetime

    def to_dict(self) -> dict[str, str]:
        return {
            "session_id": self.session_id,
            "product_id": self.product_id,
            "cart_time": self.cart_time.isoformat(),
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass(slots=True)
class SlidingWindowAnalytics:
    """Maintain exact recent counters plus delayed cart-abandonment signals.

    The class assumes replay-clock event order. Kinesis records use session_id as
    their partition key, while the AWS implementation persists equivalent
    minute-bucket counters in DynamoDB.
    """

    window: timedelta = timedelta(minutes=5)
    abandonment_timeout: timedelta = timedelta(minutes=15)
    _events: deque[ClickEvent] = field(default_factory=deque, init=False)
    _product_counts: dict[str, Counter[str]] = field(
        default_factory=lambda: defaultdict(Counter), init=False
    )
    _session_counts: dict[str, Counter[str]] = field(
        default_factory=lambda: defaultdict(Counter), init=False
    )
    _pending_carts: dict[tuple[str, str], datetime] = field(default_factory=dict, init=False)
    _signals: list[AbandonmentSignal] = field(default_factory=list, init=False)
    _latest_time: datetime | None = field(default=None, init=False)
    processed_events: int = field(default=0, init=False)

    def process(self, event: ClickEvent) -> list[AbandonmentSignal]:
        if self._latest_time is not None and event.event_time < self._latest_time:
            raise ValueError("Events must be ordered by replay event_time")

        signals = self.advance(event.event_time)
        self._events.append(event)
        self._product_counts[event.product_id][event.event_type] += 1
        self._session_counts[event.session_id][event.event_type] += 1
        self.processed_events += 1

        cart_key = (event.session_id, event.product_id)
        if event.event_type == "cart":
            self._pending_carts[cart_key] = event.event_time
        elif event.event_type in {"purchase", "remove_from_cart"}:
            self._pending_carts.pop(cart_key, None)

        self._latest_time = event.event_time
        return signals

    def advance(self, current_time: datetime) -> list[AbandonmentSignal]:
        """Advance event time, evict old events, and emit overdue cart signals."""
        if current_time.tzinfo is None:
            raise ValueError("current_time must include a timezone")
        if self._latest_time is not None and current_time < self._latest_time:
            raise ValueError("Cannot move the event clock backwards")

        window_start = current_time - self.window
        while self._events and self._events[0].event_time < window_start:
            expired = self._events.popleft()
            self._decrement(self._product_counts, expired.product_id, expired.event_type)
            self._decrement(self._session_counts, expired.session_id, expired.event_type)

        abandonment_cutoff = current_time - self.abandonment_timeout
        newly_detected: list[AbandonmentSignal] = []
        for key, cart_time in list(self._pending_carts.items()):
            if cart_time <= abandonment_cutoff:
                session_id, product_id = key
                signal = AbandonmentSignal(session_id, product_id, cart_time, current_time)
                newly_detected.append(signal)
                self._signals.append(signal)
                del self._pending_carts[key]

        self._latest_time = current_time
        return newly_detected

    @staticmethod
    def _decrement(container: dict[str, Counter[str]], key: str, event_type: str) -> None:
        counts = container[key]
        counts[event_type] -= 1
        if counts[event_type] <= 0:
            del counts[event_type]
        if not counts:
            del container[key]

    @staticmethod
    def _safe_dropoff(entered: int, continued: int) -> float | None:
        if entered == 0:
            return None
        return round(max(0.0, 1 - (continued / entered)), 4)

    def snapshot(self, top_n: int = 5) -> dict[str, Any]:
        """Return a serving-ready snapshot for the current sliding window."""
        if self._latest_time is None:
            now = datetime.now(timezone.utc)
        else:
            now = self._latest_time

        ranked: list[dict[str, Any]] = []
        totals: Counter[str] = Counter()
        for product_id, counts in self._product_counts.items():
            totals.update(counts)
            views = counts.get("view", 0)
            carts = counts.get("cart", 0)
            purchases = counts.get("purchase", 0)
            score = views + (3 * carts) + (5 * purchases)
            ranked.append(
                {
                    "product_id": product_id,
                    "trend_score": score,
                    "views": views,
                    "carts": carts,
                    "purchases": purchases,
                }
            )

        ranked.sort(key=lambda item: (-item["trend_score"], item["product_id"]))
        view_sessions = sum(1 for counts in self._session_counts.values() if counts.get("view", 0))
        cart_sessions = sum(1 for counts in self._session_counts.values() if counts.get("cart", 0))
        purchase_sessions = sum(
            1 for counts in self._session_counts.values() if counts.get("purchase", 0)
        )

        return {
            "as_of": now.isoformat(),
            "window_seconds": int(self.window.total_seconds()),
            "window_start": (now - self.window).isoformat(),
            "events_in_window": len(self._events),
            "processed_events_total": self.processed_events,
            "active_sessions": len(self._session_counts),
            "event_totals": dict(totals),
            "top_products": ranked[:top_n],
            "funnel": {
                "view_sessions": view_sessions,
                "cart_sessions": cart_sessions,
                "purchase_sessions": purchase_sessions,
                "view_to_cart_dropoff": self._safe_dropoff(view_sessions, cart_sessions),
                "cart_to_purchase_dropoff": self._safe_dropoff(cart_sessions, purchase_sessions),
            },
            "pending_carts": len(self._pending_carts),
            "abandoned_cart_signals_total": len(self._signals),
            "latest_abandoned_carts": [item.to_dict() for item in self._signals[-10:]],
        }


def read_json_lines(path: Path) -> Iterator[ClickEvent]:
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                yield ClickEvent.from_dict(json.loads(line))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid event on line {line_number}: {exc}") from exc


def analyse(events: Iterable[ClickEvent], window_minutes: int = 5) -> SlidingWindowAnalytics:
    analytics = SlidingWindowAnalytics(window=timedelta(minutes=window_minutes))
    for event in events:
        analytics.process(event)
    return analytics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Canonical JSONL emitted by the replay producer")
    parser.add_argument("--window-minutes", type=int, default=5)
    parser.add_argument("--abandonment-minutes", type=int, default=15)
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    parser.add_argument(
        "--flush-abandonment",
        action="store_true",
        help="Advance the clock after the final event to expose pending cart abandonments",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    analytics = SlidingWindowAnalytics(
        window=timedelta(minutes=args.window_minutes),
        abandonment_timeout=timedelta(minutes=args.abandonment_minutes),
    )
    for event in read_json_lines(args.input):
        analytics.process(event)
    if args.flush_abandonment and analytics._latest_time is not None:
        analytics.advance(analytics._latest_time + analytics.abandonment_timeout)

    rendered = json.dumps(analytics.snapshot(args.top), indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
