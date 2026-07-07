"""AWS Lambda handler: Kinesis records to DynamoDB one-minute speed buckets.

Package this file as the Lambda handler and configure METRICS_TABLE. The table
must have string partition/sort keys named PK and SK plus TTL on ExpiresAt.
"""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import boto3


TABLE = boto3.resource("dynamodb").Table(os.environ["METRICS_TABLE"])
RETENTION_HOURS = int(os.environ.get("RETENTION_HOURS", "48"))
METRIC_NAMES = {
    "view": "Views",
    "cart": "Carts",
    "remove_from_cart": "Removals",
    "purchase": "Purchases",
}


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _minute_bucket(value: datetime) -> str:
    return value.replace(second=0, microsecond=0).isoformat()


def _update_product(event: dict, event_time: datetime) -> None:
    metric = METRIC_NAMES[event["event_type"]]
    expires_at = int((event_time + timedelta(hours=RETENTION_HOURS)).timestamp())
    TABLE.update_item(
        Key={"PK": f"WINDOW#{_minute_bucket(event_time)}", "SK": f"PRODUCT#{event['product_id']}"},
        UpdateExpression="ADD #metric :one SET ExpiresAt = :ttl, UpdatedAt = :updated",
        ExpressionAttributeNames={"#metric": metric},
        ExpressionAttributeValues={
            ":one": Decimal(1),
            ":ttl": Decimal(expires_at),
            ":updated": datetime.now(timezone.utc).isoformat(),
        },
    )


def _update_health(event_time: datetime, experiment_id: str | None = None) -> int:
    now = datetime.now(timezone.utc)
    latency_ms = max(0, int((now - event_time).total_seconds() * 1000))
    expires_at = int((event_time + timedelta(hours=RETENTION_HOURS)).timestamp())
    TABLE.update_item(
        Key={
            "PK": f"WINDOW#{_minute_bucket(event_time)}",
            "SK": f"HEALTH#{experiment_id}" if experiment_id else "HEALTH",
        },
        UpdateExpression=(
            "ADD EventCount :one, LatencyTotalMs :latency "
            "SET ExpiresAt = :ttl, UpdatedAt = :updated"
        ),
        ExpressionAttributeValues={
            ":one": Decimal(1),
            ":latency": Decimal(latency_ms),
            ":ttl": Decimal(expires_at),
            ":updated": now.isoformat(),
        },
    )
    return latency_ms


def lambda_handler(event: dict, _context: object) -> dict:
    failures: list[dict[str, str]] = []
    for record in event.get("Records", []):
        sequence_number = record.get("kinesis", {}).get("sequenceNumber", "unknown")
        try:
            payload = base64.b64decode(record["kinesis"]["data"])
            click = json.loads(payload)
            if click["event_type"] not in METRIC_NAMES:
                raise ValueError("unsupported event_type")
            event_time = _time(click["event_time"])
            _update_product(click, event_time)
            experiment_id = click.get("experiment_id")
            latency_ms = _update_health(event_time, experiment_id)
            print(
                json.dumps(
                    {
                        "metric": "clickstream_processing_latency",
                        "experiment_id": experiment_id or "unlabelled",
                        "latency_ms": latency_ms,
                        "event_type": click["event_type"],
                    },
                    separators=(",", ":"),
                )
            )
        except Exception:  # Lambda reports the failed sequence for retry
            failures.append({"itemIdentifier": sequence_number})
    return {"batchItemFailures": failures}
