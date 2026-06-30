#!/usr/bin/env python3
"""Build historical five-minute product baselines with PySpark.

Example on EMR:
    spark-submit --deploy-mode cluster jobs/batch_baseline.py \
      s3://BUCKET/raw/events/ s3://BUCKET/batch/product-baselines/
"""

from __future__ import annotations

import argparse

from pyspark.sql import SparkSession, functions as F


def build_baseline(input_path: str, output_path: str, partitions: int | None = None) -> None:
    spark = SparkSession.builder.appName("clickstream-product-baselines").getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")

    events = (
        spark.read.json(input_path)
        .select(
            F.coalesce(F.to_timestamp("source_event_time"), F.to_timestamp("event_time")).alias(
                "event_time"
            ),
            F.col("event_type"),
            F.col("product_id").cast("string").alias("product_id"),
            F.col("session_id").cast("string").alias("session_id"),
        )
        .filter(
            F.col("event_time").isNotNull()
            & F.col("product_id").isNotNull()
            & F.col("session_id").isNotNull()
            & F.col("event_type").isin("view", "cart", "remove_from_cart", "purchase")
        )
    )
    if partitions:
        events = events.repartition(partitions, "product_id")

    windowed = (
        events.groupBy("product_id", F.window("event_time", "5 minutes").alias("time_window"))
        .pivot("event_type", ["view", "cart", "remove_from_cart", "purchase"])
        .count()
        .na.fill(0)
        .withColumnRenamed("view", "views")
        .withColumnRenamed("cart", "carts")
        .withColumnRenamed("purchase", "purchases")
        .withColumn("trend_score", F.col("views") + 3 * F.col("carts") + 5 * F.col("purchases"))
    )

    activity_baseline = windowed.groupBy("product_id").agg(
        F.avg("views").alias("avg_views_5m"),
        F.avg("carts").alias("avg_carts_5m"),
        F.avg("purchases").alias("avg_purchases_5m"),
        F.avg("trend_score").alias("avg_trend_score_5m"),
        F.sum("views").alias("total_views"),
        F.sum("carts").alias("total_carts"),
        F.sum("purchases").alias("total_purchases"),
        F.count("*").alias("observed_5m_windows"),
    )

    sessions = events.groupBy("product_id").agg(
        F.countDistinct(F.when(F.col("event_type") == "view", F.col("session_id"))).alias(
            "view_sessions"
        ),
        F.countDistinct(F.when(F.col("event_type") == "cart", F.col("session_id"))).alias(
            "cart_sessions"
        ),
        F.countDistinct(F.when(F.col("event_type") == "purchase", F.col("session_id"))).alias(
            "purchase_sessions"
        ),
    )

    baseline = (
        activity_baseline.join(sessions, "product_id", "left")
        .withColumn(
            "historical_view_to_cart_dropoff",
            F.when(F.col("view_sessions") > 0, 1 - F.col("cart_sessions") / F.col("view_sessions")),
        )
        .withColumn(
            "historical_cart_to_purchase_dropoff",
            F.when(
                F.col("cart_sessions") > 0,
                1 - F.col("purchase_sessions") / F.col("cart_sessions"),
            ),
        )
    )

    baseline.write.mode("overwrite").parquet(output_path.rstrip("/") + "/parquet")
    baseline.coalesce(1).write.mode("overwrite").json(output_path.rstrip("/") + "/json")
    spark.stop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Canonical JSON/JSONL input path (local or S3)")
    parser.add_argument("output", help="Output directory (local or S3)")
    parser.add_argument("--partitions", type=int, help="Explicit data partitions for benchmarks")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    build_baseline(arguments.input, arguments.output, arguments.partitions)
