# Controlled load and auto-scaling experiments

These experiments close the two remaining technical evidence gaps without changing the analytical question. Run them only inside the active AWS Academy Learner Lab in `us-east-1`.

## 1. Refresh the Lambda package

The speed Lambda now writes one small structured CloudWatch log line per processed event. It contains only the experiment label, event type and processing latency; it does not contain a user or session identifier.

```bash
cd ~/clickstream-analytics
chmod +x scripts/cloudshell_deploy.sh
./scripts/cloudshell_deploy.sh
```

Confirm that the Kinesis event-source mapping is `Enabled` before starting the measurements.

## 2. Measure speed-layer latency under three loads

The script performs three repeats at 100, 500 and 1,000 events per second. Every replay receives a separate experiment label. CloudWatch Logs Insights returns processed count, average latency, p50 latency, p95 latency and maximum latency. The script also records the Lambda iterator-age backlog metric observed around each Kinesis-triggered run.

```bash
export PYTHONPATH=$PWD/src
python3 scripts/run_stream_load_experiment.py \
  data/raw/electronics-events.csv.gz \
  --stream scp-clickstream-events \
  --function scp-clickstream-speed \
  --region us-east-1 \
  --rates 100 500 1000 \
  --records 1000 \
  --repeats 3 \
  --output benchmarks/stream_load_results.csv
```

Do not report a run as complete when `processed_records` is lower than `sent_records`. Either rerun that configuration or explain the loss/error explicitly.

Generate the assessment figure after the CSV has been copied to a machine with matplotlib:

```bash
python3 scripts/plot_stream_load_results.py \
  benchmarks/stream_load_results.csv \
  output/assets/stream_load_performance.png
```

The plotter refuses to create a figure when no complete run exists, preventing placeholder measurements from entering the report. It produces latency versus ingestion rate, throughput versus target rate, and throughput over experiment time.

## 3. Capture an EMR managed-scaling action

Use two CloudShell tabs. In the first tab, monitor the existing cluster for 15 minutes:

```bash
chmod +x scripts/monitor_emr_scaling.sh
scripts/monitor_emr_scaling.sh CLUSTER_ID 900 benchmarks/emr_scaling_events.csv
```

In the second tab, submit a sustained PySpark workload against a larger input prefix. Keep the deployed managed-scaling range at two to four workers. The workload must use the same batch program and should run long enough for EMR to evaluate the backlog; a 58-second step is too short.

Record these items together:

- cluster ID and managed-scaling minimum/maximum;
- Spark input size and partition count;
- step start and finish times;
- `benchmarks/emr_scaling_events.csv`;
- a console screenshot or CloudWatch view showing the worker-count change;
- whether backlog/step duration recovered after scale-out.

The monitor prints a positive result only when the total core/task worker count changes. If it remains constant, the correct conclusion is that the policy was configured but scale-out was not observed.

## 4. Compare batch speedup by worker count

Worker scaling and partition scaling are different experiments. For the worker-count comparison, run the same PySpark input and the same partition count at two or more fixed worker counts. Repeat each configuration and record only completed EMR steps in `benchmarks/emr_worker_benchmark.csv`:

```csv
worker_count,repeat,duration_seconds,status,input_events,partitions
2,1,58,COMPLETED,999825,8
```

The example above documents the already verified two-worker run; it is not enough to form a scaling curve. Add measured rows for other worker counts only after those steps complete. Then generate the required speedup-versus-worker-count figure:

```bash
python3 scripts/plot_emr_worker_results.py \
  benchmarks/emr_worker_benchmark.csv \
  output/assets/emr_worker_speedup.png
```

The plotter requires at least two distinct completed worker counts and otherwise exits without creating a chart.

## 5. Report wording

Only after the resulting files exist should the report claim measured latency under load or an observed scale-out. Until then, use these statements:

- “The controlled load experiment is prepared but not yet executed in an active Learner Lab session.”
- “EMR managed scaling was configured for two to four workers; an observed worker-count change has not yet been captured.”

This distinction keeps configured capability separate from measured behaviour.
