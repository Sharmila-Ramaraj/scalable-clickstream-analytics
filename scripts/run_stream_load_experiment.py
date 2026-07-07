#!/usr/bin/env python3
"""Measure Kinesis-to-Lambda latency at controlled replay rates.

Run this from AWS CloudShell after the project stack and updated Lambda have
been deployed. Each run receives an experiment label, allowing CloudWatch Logs
Insights to calculate latency percentiles without mixing test configurations.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from clickstream_analytics.producer import KinesisSink, read_rees46, replay  # noqa: E402


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="REES46 CSV or CSV.GZ input")
    parser.add_argument("--stream", default="scp-clickstream-events")
    parser.add_argument("--function", default="scp-clickstream-speed")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--rates", type=int, nargs="+", default=[100, 500, 1000])
    parser.add_argument("--records", type=int, default=1000, help="Valid records per run")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=120, help="Seconds to wait for logs")
    parser.add_argument("--output", type=Path, default=ROOT / "benchmarks" / "stream_load_results.csv")
    return parser.parse_args()


def result_value(rows: list[list[dict[str, str]]], field: str) -> float | None:
    if not rows:
        return None
    values = {item["field"]: item.get("value", "") for item in rows[0]}
    try:
        return float(values[field])
    except (KeyError, TypeError, ValueError):
        return None


def query_latency(logs, log_group: str, experiment_id: str, start: int, end: int):
    query = (
        "fields @message "
        f'| filter @message like /{experiment_id}/ '
        '| parse @message /"latency_ms":(?<latency_ms>[0-9]+)/ '
        "| stats count(*) as processed, avg(latency_ms) as avg_latency_ms, "
        "pct(latency_ms, 50) as p50_latency_ms, "
        "pct(latency_ms, 95) as p95_latency_ms, max(latency_ms) as max_latency_ms"
    )
    query_id = logs.start_query(
        logGroupName=log_group,
        startTime=start,
        endTime=end,
        queryString=query,
        limit=20,
    )["queryId"]
    while True:
        response = logs.get_query_results(queryId=query_id)
        if response["status"] in {"Complete", "Failed", "Cancelled", "Timeout"}:
            return response
        time.sleep(1)


def wait_for_latency(logs, log_group: str, experiment_id: str, start: int, expected: int, timeout: int):
    deadline = time.monotonic() + timeout
    latest = None
    while time.monotonic() < deadline:
        latest = query_latency(logs, log_group, experiment_id, start - 30, int(time.time()) + 30)
        processed = result_value(latest.get("results", []), "processed") or 0
        if processed >= expected:
            return latest
        time.sleep(5)
    return latest or {"status": "Timeout", "results": []}


def iterator_age(cloudwatch, function_name: str, start: datetime, end: datetime) -> float | None:
    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/Lambda",
        MetricName="IteratorAge",
        Dimensions=[{"Name": "FunctionName", "Value": function_name}],
        StartTime=start - timedelta(minutes=1),
        EndTime=end + timedelta(minutes=1),
        Period=60,
        Statistics=["Maximum"],
    )
    points = [float(point["Maximum"]) for point in response.get("Datapoints", [])]
    return max(points) if points else None


def main() -> int:
    args = arguments()
    try:
        import boto3
    except ImportError as exc:
        raise SystemExit("boto3 is required; run this script in AWS CloudShell") from exc

    logs = boto3.client("logs", region_name=args.region)
    cloudwatch = boto3.client("cloudwatch", region_name=args.region)
    log_group = f"/aws/lambda/{args.function}"
    rows: list[dict[str, object]] = []

    for rate in args.rates:
        for repeat in range(1, args.repeats + 1):
            experiment_id = f"rate-{rate}-run-{repeat}-{int(time.time())}"
            started_at = datetime.now(timezone.utc)
            started_epoch = int(started_at.timestamp())
            sink = KinesisSink(
                args.stream,
                region=args.region,
                batch_size=100,
                experiment_id=experiment_id,
            )
            clock_start = time.monotonic()
            sent = replay(
                read_rees46(args.input, limit=args.records),
                sink,
                events_per_second=rate,
                sleep=True,
            )
            producer_seconds = time.monotonic() - clock_start
            completed_at = datetime.now(timezone.utc)
            query_result = wait_for_latency(
                logs,
                log_group,
                experiment_id,
                started_epoch,
                sent,
                args.timeout,
            )
            results = query_result.get("results", [])
            processed = int(result_value(results, "processed") or 0)
            row = {
                "experiment_id": experiment_id,
                "started_at_utc": started_at.isoformat(),
                "completed_at_utc": completed_at.isoformat(),
                "target_rate_eps": rate,
                "repeat": repeat,
                "sent_records": sent,
                "processed_records": processed,
                "producer_seconds": round(producer_seconds, 3),
                "producer_throughput_eps": round(sent / producer_seconds, 2),
                "avg_latency_ms": result_value(results, "avg_latency_ms"),
                "p50_latency_ms": result_value(results, "p50_latency_ms"),
                "p95_latency_ms": result_value(results, "p95_latency_ms"),
                "max_latency_ms": result_value(results, "max_latency_ms"),
                "max_iterator_age_ms": iterator_age(cloudwatch, args.function, started_at, completed_at),
                "query_status": query_result.get("status", "Unknown"),
            }
            rows.append(row)
            print(
                f"{experiment_id}: sent={sent}, processed={processed}, "
                f"p95={row['p95_latency_ms']} ms, throughput={row['producer_throughput_eps']} events/s"
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} controlled run(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
