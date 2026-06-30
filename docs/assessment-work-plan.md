# Assessment work plan

## Phase 1 - Design and setup (20 marks)

- Use case and Lambda justification: `docs/project-specification.md`
- Architecture diagram and scaling boundary: `docs/architecture.md`
- AWS resources: Kinesis, S3, DynamoDB, Lambda and EMR
- Evidence to capture: resource configuration, incoming records, architecture diagram, scaling settings

## Phase 2 - Parallel processing (45 marks)

### Batch layer

- Run `jobs/batch_baseline.py` over the accumulated raw history.
- Validate totals against a small hand-calculated fixture.
- Record one-worker and multi-worker duration using identical input.

### Speed layer

- Use one-minute DynamoDB buckets and merge the latest five for a sliding view.
- Display top products, lift and both funnel drop-off rates.
- Demonstrate updates while the producer is running.

### Hybrid and serving

- Join recent product metrics to Spark historical baselines.
- Flag products at or above the chosen lift threshold.
- Record latency as ingestion rate increases.

## Phase 3 - Measurement and reporting (35 marks)

Run a controlled matrix and repeat every configuration at least three times:

| Experiment | Independent variable | Primary outputs |
|---|---|---|
| Stream load | 100, 500, 1,000 events/s or the maximum stable lab rates | p50/p95 latency, throughput, backlog, errors |
| Batch scale | 1, 2, and 4 workers | duration, speedup, efficiency |
| Data size | 100k, 500k, and 1m events | duration and scaling trend |
| Elasticity | sudden low-high-low replay pattern | scaling time, backlog recovery, cost/resource trade-off |

Required calculations:

```text
speedup(N) = T(1) / T(N)
efficiency(N) = speedup(N) / N
```

Produce at least these graphs:

1. Speedup versus Spark worker count.
2. p50/p95 speed-layer latency versus ingestion rate.
3. Ingested and processed throughput over time.
4. Kinesis backlog and worker count during the elasticity experiment.

## Report structure (IEEE, maximum 10 pages)

1. Abstract and keywords
2. Introduction and objectives
3. Related work and Lambda architecture justification
4. Dataset and methodology
5. System architecture and implementation
6. Experimental design
7. Results
8. Critical analysis, limitations and improvements
9. Conclusion
10. References

## Evidence checklist

- GitHub link and reproducible README
- Dataset citation and preprocessing description
- Architecture diagram with the scaling boundary
- Kinesis records visibly arriving
- Batch and speed outputs
- Merged serving result
- Auto-scaling event or managed-scaling evidence
- Raw benchmark CSV files and generated graphs
- Clear sequential-versus-parallel comparison
- Video showing the live path rather than only static screenshots
