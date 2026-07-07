#!/usr/bin/env python3
"""Plot EMR duration and speedup from completed worker-count trials."""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("Install matplotlib to generate the EMR worker figure") from exc

    trials: dict[int, list[float]] = defaultdict(list)
    with args.input.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row.get("status", "COMPLETED").upper() != "COMPLETED":
                continue
            workers = int(row["worker_count"])
            duration = float(row["duration_seconds"])
            if workers > 0 and duration > 0:
                trials[workers].append(duration)

    workers = sorted(trials)
    if len(workers) < 2:
        raise SystemExit(
            "At least two completed worker counts are required; do not plot placeholder data"
        )

    durations = [statistics.median(trials[count]) for count in workers]
    baseline = durations[0]
    speedups = [baseline / duration for duration in durations]

    figure, axes = plt.subplots(1, 2, figsize=(9, 4.2))
    axes[0].plot(workers, durations, marker="o", color="#2167a8")
    axes[0].set(
        xlabel="EMR worker count",
        ylabel="Median duration (seconds)",
        title="Batch duration by worker count",
        xticks=workers,
    )
    axes[0].grid(alpha=.25)
    axes[1].plot(workers, speedups, marker="o", color="#168466", label="Measured")
    axes[1].plot(workers, [count / workers[0] for count in workers], linestyle="--", color="#7d8796", label="Ideal")
    axes[1].set(
        xlabel="EMR worker count",
        ylabel="Speedup relative to smallest cluster",
        title="Speedup versus worker count",
        xticks=workers,
    )
    axes[1].grid(alpha=.25)
    axes[1].legend()
    figure.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=180)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
