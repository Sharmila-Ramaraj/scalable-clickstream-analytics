#!/usr/bin/env python3
"""Plot latency by load and throughput over time from controlled AWS runs."""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("Install matplotlib to generate the load-test figure") from exc

    grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
    completed_rows: list[dict[str, str]] = []
    with args.input.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if (
                row.get("p95_latency_ms")
                and row.get("completed_at_utc")
                and row.get("processed_records") == row.get("sent_records")
            ):
                grouped[int(row["target_rate_eps"])].append(row)
                completed_rows.append(row)
    if not grouped:
        raise SystemExit("No completed latency rows were found; do not plot placeholder data")

    rates = sorted(grouped)
    median = lambda field, rate: statistics.median(float(row[field]) for row in grouped[rate])
    p50 = [median("p50_latency_ms", rate) for rate in rates]
    p95 = [median("p95_latency_ms", rate) for rate in rates]
    throughput = [median("producer_throughput_eps", rate) for rate in rates]

    completed_rows.sort(key=lambda row: row["completed_at_utc"])
    times = [datetime.fromisoformat(row["completed_at_utc"]) for row in completed_rows]
    elapsed_minutes = [(value - times[0]).total_seconds() / 60 for value in times]
    observed_throughput = [float(row["producer_throughput_eps"]) for row in completed_rows]

    figure, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    axes[0].plot(rates, p50, marker="o", label="p50 latency")
    axes[0].plot(rates, p95, marker="o", label="p95 latency")
    axes[0].set(xlabel="Target ingestion rate (events/s)", ylabel="Latency (ms)", title="Speed-layer latency under load")
    axes[0].grid(alpha=.25)
    axes[0].legend()
    axes[1].bar([str(rate) for rate in rates], throughput, color="#2167a8")
    axes[1].set(xlabel="Target ingestion rate (events/s)", ylabel="Observed producer throughput (events/s)", title="Observed ingestion throughput")
    axes[1].grid(axis="y", alpha=.25)
    axes[2].plot(elapsed_minutes, observed_throughput, marker="o", color="#168466")
    axes[2].set(xlabel="Elapsed experiment time (minutes)", ylabel="Observed throughput (events/s)", title="Throughput over time")
    axes[2].grid(alpha=.25)
    figure.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=180)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
