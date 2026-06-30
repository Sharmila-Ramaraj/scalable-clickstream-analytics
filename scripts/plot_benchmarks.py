#!/usr/bin/env python3
"""Create the report-ready EMR duration and speedup figure."""

from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "benchmarks" / "emr_results.csv"
OUTPUT = ROOT / "benchmarks" / "emr_performance.png"


with INPUT.open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream))

labels = [row["configuration"] for row in rows]
durations = [float(row["duration_seconds"]) for row in rows]
speedups = [float(row["speedup"]) for row in rows]
colors = ["#6b7280", "#2563eb"]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    name = "Arial Bold.ttf" if bold else "Arial.ttf"
    path = Path("/System/Library/Fonts/Supplemental") / name
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()


canvas = Image.new("RGB", (1800, 720), "white")
draw = ImageDraw.Draw(canvas)
title_font = font(38, bold=True)
heading_font = font(30, bold=True)
label_font = font(23)
value_font = font(25, bold=True)
small_font = font(20)

main_title = "PySpark benchmark: 999,825 clickstream events, two initial workers"
draw.text((900, 35), main_title, fill="#111827", font=title_font, anchor="ma")


def panel(
    left: int,
    right: int,
    heading: str,
    values: list[float],
    value_labels: list[str],
    maximum: float,
    reference: float | None = None,
) -> None:
    top, bottom = 150, 570
    draw.text(((left + right) / 2, 105), heading, fill="#111827", font=heading_font, anchor="ma")
    for tick in range(5):
        y = bottom - tick * (bottom - top) / 4
        tick_value = maximum * tick / 4
        draw.line((left, y, right, y), fill="#d1d5db", width=2)
        draw.text((left - 15, y), f"{tick_value:.1f}", fill="#4b5563", font=small_font, anchor="rm")

    if reference is not None:
        y = bottom - (reference / maximum) * (bottom - top)
        draw.line((left, y, right, y), fill="#111827", width=3)

    bar_width = 150
    centres = [left + (right - left) * 0.32, left + (right - left) * 0.72]
    for centre, value, value_label, label, colour in zip(
        centres, values, value_labels, labels, colors, strict=True
    ):
        bar_top = bottom - (value / maximum) * (bottom - top)
        draw.rounded_rectangle(
            (centre - bar_width / 2, bar_top, centre + bar_width / 2, bottom),
            radius=8,
            fill=colour,
        )
        draw.text((centre, bar_top - 12), value_label, fill="#111827", font=value_font, anchor="ms")
        draw.text((centre, bottom + 28), label, fill="#374151", font=label_font, anchor="ma")


panel(130, 835, "EMR batch duration", durations, [f"{v:.0f} s" for v in durations], 80)
panel(1020, 1725, "Relative speedup", speedups, [f"{v:.3f}x" for v in speedups], 1.4, 1.0)
draw.text((480, 675), "Elapsed time (lower is better)", fill="#4b5563", font=label_font, anchor="ma")
draw.text((1370, 675), "T(1 partition) / T(configuration)", fill="#4b5563", font=label_font, anchor="ma")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
canvas.save(OUTPUT, format="PNG", optimize=True)
