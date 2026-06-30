#!/usr/bin/env python3
"""Single-process reference implementation of the historical baseline.

This is used for correctness checks and T(1) benchmark comparisons. The
distributed production implementation is batch_baseline.py (PySpark).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from clickstream_analytics.models import ClickEvent
from clickstream_analytics.speed import read_json_lines


def _window_start(event: ClickEvent) -> int:
    historical_time = event.source_event_time or event.event_time
    epoch = int(historical_time.timestamp())
    return epoch - (epoch % 300)


def calculate(events: Iterable[ClickEvent]) -> list[dict[str, Any]]:
    windows: dict[tuple[str, int], Counter[str]] = defaultdict(Counter)
    sessions: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

    for event in events:
        windows[(event.product_id, _window_start(event))][event.event_type] += 1
        sessions[event.product_id][event.event_type].add(event.session_id)

    product_windows: dict[str, list[Counter[str]]] = defaultdict(list)
    for (product_id, _), counts in windows.items():
        product_windows[product_id].append(counts)

    rows: list[dict[str, Any]] = []
    for product_id, observed in sorted(product_windows.items()):
        count = len(observed)
        totals = sum(observed, Counter())
        scores = [
            values.get("view", 0)
            + 3 * values.get("cart", 0)
            + 5 * values.get("purchase", 0)
            for values in observed
        ]
        view_sessions = len(sessions[product_id]["view"])
        cart_sessions = len(sessions[product_id]["cart"])
        purchase_sessions = len(sessions[product_id]["purchase"])
        rows.append(
            {
                "product_id": product_id,
                "avg_views_5m": totals.get("view", 0) / count,
                "avg_carts_5m": totals.get("cart", 0) / count,
                "avg_purchases_5m": totals.get("purchase", 0) / count,
                "avg_trend_score_5m": sum(scores) / count,
                "total_views": totals.get("view", 0),
                "total_carts": totals.get("cart", 0),
                "total_purchases": totals.get("purchase", 0),
                "observed_5m_windows": count,
                "view_sessions": view_sessions,
                "cart_sessions": cart_sessions,
                "purchase_sessions": purchase_sessions,
                "historical_view_to_cart_dropoff": (
                    1 - cart_sessions / view_sessions if view_sessions else None
                ),
                "historical_cart_to_purchase_dropoff": (
                    1 - purchase_sessions / cart_sessions if cart_sessions else None
                ),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = calculate(read_json_lines(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
