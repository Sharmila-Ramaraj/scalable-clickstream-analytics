# Verified AWS results - 3 August 2026

## Environment

- Region: `us-east-1`
- Architecture resources: Amazon Kinesis Data Streams, AWS Lambda, DynamoDB, Amazon S3, and Amazon EMR on EC2
- EMR release: `emr-7.13.0`
- Spark version: 3.5.6
- EMR capacity at launch: one primary, one core worker, and one task worker
- Managed scaling: minimum 2 workers, maximum 4 workers, maximum 1 core worker
- Safety control: automatic termination after 20 idle minutes; the cluster was also terminated manually after the benchmark

## Dataset preparation

- Source: REES46 public electronics e-commerce behaviour events
- Source rows: 885,129 events plus the CSV header
- Historical subset inspected: first 200,000 rows
- Valid canonical events: 199,965
- Rejected rows: 35 (0.0175%) because `user_session` was absent
- Canonical subset size: 58 MB JSONL
- Normalisation/replay-file generation: 16.804 seconds
- EMR benchmark input: five S3-side copies of the valid subset
- Total benchmark events: 999,825
- Approximate benchmark input size: 290 MB

Rejecting rows without a session identifier is necessary because funnel transitions and abandonment signals cannot be attributed to a shopping session without that field.

## Live speed-layer verification

- The Kinesis-to-Lambda event-source mapping reached `Enabled`.
- A replayed batch was consumed successfully.
- DynamoDB contained three aggregate rows for the demonstration window (two product rows and one health row).
- Product 200 had a current trend score of 5 against a historical average of 2.5, producing an activity lift of 2.0 and an unusual-trend flag.
- Product 100 had a current score of 13 against a baseline of 13, producing a lift of 1.0 and no unusual-trend flag.
- Current view-to-cart drop-off: 25%.
- Current cart-to-purchase drop-off: 66.67%.

## PySpark batch benchmark

Both executions used the same EMR cluster and the same 999,825-event input.

| Configuration | Partitions | Duration | Relative speedup |
|---|---:|---:|---:|
| Sequential reference | 1 | 70 s | 1.000x |
| Parallel execution | 8 | 58 s | 1.207x |

The observed improvement was 12 seconds (17.1% lower elapsed time). Speedup was calculated as `70 / 58 = 1.207`. The result is below linear speedup because input parsing, Spark job start-up, S3 I/O, shuffles, task scheduling, and final coalescing remain serial or coordination-heavy. The input was also modest for a distributed cluster, so fixed Spark overhead represented a significant proportion of elapsed time.

## Output verification

The parallel job completed with `_SUCCESS` markers for both output formats. It produced:

- two compressed Parquet part files;
- one consolidated JSON result file;
- approximately 9.75 MB of total batch output;
- EMR controller, standard output, standard error, and system logs retained in S3/CloudWatch.

## Critical limitations

- The benchmark compares one and eight Spark partitions on the same two-worker cluster; it is a sequential-versus-parallel execution comparison, not a controlled worker-count scaling experiment.
- The managed-scaling policy was configured and verified, but the short benchmark did not provide enough sustained backlog to prove a scale-out event.
- The initial live demonstration used eight deterministic events for correctness before the larger public dataset was prepared.
- DynamoDB minute buckets use atomic increments; a production implementation should add idempotency keys to prevent duplicate counting after Kinesis retries.
