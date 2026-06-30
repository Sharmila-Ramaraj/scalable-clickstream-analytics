"""Replay an historical clickstream into stdout, JSONL, or Amazon Kinesis."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Iterator, Protocol, TextIO

from .models import ClickEvent


class Sink(Protocol):
    def send(self, event: ClickEvent) -> None: ...
    def close(self) -> None: ...


class JsonLinesSink:
    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def send(self, event: ClickEvent) -> None:
        self.stream.write(json.dumps(event.to_dict(), separators=(",", ":")) + "\n")

    def close(self) -> None:
        self.stream.flush()


class KinesisSink:
    """Small buffered Kinesis producer; records are partitioned by session."""

    def __init__(self, stream_name: str, region: str | None = None, batch_size: int = 100) -> None:
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - depends on optional package
            raise RuntimeError("Install the 'aws' project extra to use Kinesis") from exc
        self.client = boto3.client("kinesis", region_name=region)
        self.stream_name = stream_name
        self.batch_size = batch_size
        self.records: list[dict[str, bytes | str]] = []

    def send(self, event: ClickEvent) -> None:
        self.records.append(
            {
                # Newline-delimited JSON remains directly readable when Data Firehose
                # concatenates Kinesis records into buffered S3 objects.
                "Data": (json.dumps(event.to_dict(), separators=(",", ":")) + "\n").encode(
                    "utf-8"
                ),
                "PartitionKey": event.session_id,
            }
        )
        if len(self.records) >= self.batch_size:
            self._flush()

    def _flush(self) -> None:
        if not self.records:
            return
        response = self.client.put_records(StreamName=self.stream_name, Records=self.records)
        failures = int(response.get("FailedRecordCount", 0))
        if failures:
            raise RuntimeError(f"Kinesis rejected {failures} record(s); replay stopped")
        self.records.clear()

    def close(self) -> None:
        self._flush()


def open_csv(path: Path) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, mode="rt", encoding="utf-8", newline="")
    return path.open(mode="r", encoding="utf-8", newline="")


def read_rees46(path: Path, limit: int | None = None) -> Iterator[ClickEvent]:
    with open_csv(path) as stream:
        reader = csv.DictReader(stream)
        required = {"event_time", "event_type", "product_id", "user_id", "user_session"}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
        for index, row in enumerate(reader):
            if limit is not None and index >= limit:
                break
            try:
                yield ClickEvent.from_rees46(row)
            except (KeyError, TypeError, ValueError) as exc:
                print(f"Skipping row {index + 2}: {exc}", file=sys.stderr)


def replay(
    events: Iterable[ClickEvent],
    sink: Sink,
    events_per_second: float,
    preserve_timing: bool = False,
    sleep: bool = True,
) -> int:
    """Replay events and rebase their timestamps onto the current UTC clock."""
    if events_per_second <= 0:
        raise ValueError("events_per_second must be greater than zero")

    first_source_time: datetime | None = None
    replay_start = datetime.now(timezone.utc)
    monotonic_start = time.monotonic()
    count = 0

    try:
        for count, event in enumerate(events, start=1):
            if first_source_time is None:
                first_source_time = event.event_time

            if preserve_timing:
                offset = (event.event_time - first_source_time).total_seconds() / events_per_second
            else:
                offset = (count - 1) / events_per_second

            target = monotonic_start + offset
            if sleep:
                delay = target - time.monotonic()
                if delay > 0:
                    time.sleep(delay)

            sink.send(event.rebased(replay_start + timedelta(seconds=offset)))
    finally:
        sink.close()
    return count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="REES46 CSV or CSV.GZ file")
    parser.add_argument("--rate", type=float, default=100, help="Replay rate in events/second")
    parser.add_argument("--limit", type=int, help="Maximum records to replay")
    parser.add_argument("--preserve-timing", action="store_true", help="Preserve relative source gaps, accelerated by --rate")
    parser.add_argument("--no-sleep", action="store_true", help="Emit immediately while retaining simulated timestamps")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--output", type=Path, help="Write canonical JSONL to this file")
    output.add_argument("--kinesis-stream", help="Send records to this Kinesis stream")
    parser.add_argument("--region", help="AWS region for Kinesis")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_stream: TextIO | None = None
    if args.kinesis_stream:
        sink: Sink = KinesisSink(args.kinesis_stream, region=args.region)
    elif args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        output_stream = args.output.open("w", encoding="utf-8")
        sink = JsonLinesSink(output_stream)
    else:
        sink = JsonLinesSink(sys.stdout)

    try:
        count = replay(
            read_rees46(args.input, args.limit),
            sink,
            events_per_second=args.rate,
            preserve_timing=args.preserve_timing,
            sleep=not args.no_sleep,
        )
    finally:
        if output_stream is not None:
            output_stream.close()
    print(f"Replayed {count} event(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
