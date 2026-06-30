"""Merge recent speed-layer metrics with historical batch baselines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


def _ratio(current: int | float, baseline: int | float) -> float | None:
    if baseline <= 0:
        return None
    return round(current / baseline, 3)


def merge_views(
    speed: Mapping[str, Any], baseline_rows: list[Mapping[str, Any]], top_n: int = 5
) -> dict[str, Any]:
    """Enrich recent products with their normal five-minute activity."""
    baselines = {str(row["product_id"]): row for row in baseline_rows}
    products: list[dict[str, Any]] = []
    for recent in speed.get("top_products", []):
        product_id = str(recent["product_id"])
        baseline = baselines.get(product_id, {})
        normal_score = float(baseline.get("avg_trend_score_5m", 0) or 0)
        current_score = float(recent.get("trend_score", 0) or 0)
        products.append(
            {
                **recent,
                "normal_views_5m": round(float(baseline.get("avg_views_5m", 0) or 0), 3),
                "normal_carts_5m": round(float(baseline.get("avg_carts_5m", 0) or 0), 3),
                "normal_purchases_5m": round(
                    float(baseline.get("avg_purchases_5m", 0) or 0), 3
                ),
                "normal_trend_score_5m": round(normal_score, 3),
                "activity_lift": _ratio(current_score, normal_score),
                "is_unusually_trending": normal_score > 0 and current_score >= 2 * normal_score,
            }
        )

    products.sort(
        key=lambda item: (
            -(item["activity_lift"] if item["activity_lift"] is not None else -1),
            -item["trend_score"],
        )
    )
    return {
        "as_of": speed.get("as_of"),
        "definition": "Unusually trending means current score is at least 2x its historical five-minute average.",
        "trending_products": products[:top_n],
        "funnel": speed.get("funnel", {}),
        "abandoned_cart_signals_total": speed.get("abandoned_cart_signals_total", 0),
        "performance": {
            "events_in_window": speed.get("events_in_window", 0),
            "processed_events_total": speed.get("processed_events_total", 0),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("speed", type=Path, help="Speed-layer snapshot JSON")
    parser.add_argument("baseline", type=Path, help="Batch baseline JSON array")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    speed = json.loads(args.speed.read_text(encoding="utf-8"))
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    result = json.dumps(merge_views(speed, baseline, args.top), indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result + "\n", encoding="utf-8")
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
