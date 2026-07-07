#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 CLUSTER_ID [DURATION_SECONDS] [OUTPUT_CSV]" >&2
  exit 2
fi

TASK_CLUSTER_ID="$1"
TASK_DURATION="${2:-900}"
TASK_OUTPUT="${3:-benchmarks/emr_scaling_events.csv}"
TASK_REGION="${AWS_REGION:-us-east-1}"
TASK_INTERVAL=30
TASK_STARTED="$(date +%s)"
TASK_DEADLINE="$((TASK_STARTED + TASK_DURATION))"

mkdir -p "$(dirname "${TASK_OUTPUT}")"
echo "timestamp_utc,elapsed_seconds,core_workers,task_workers,total_workers" > "${TASK_OUTPUT}"

echo "Monitoring EMR workers for ${TASK_DURATION} seconds. Submit the sustained Spark workload in a second CloudShell tab."
while [[ "$(date +%s)" -le "${TASK_DEADLINE}" ]]; do
  TASK_NOW="$(date +%s)"
  TASK_TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  TASK_CORE="$(aws emr list-instances --cluster-id "${TASK_CLUSTER_ID}" --instance-group-types CORE --instance-states RUNNING WAITING --query 'length(Instances)' --output text --region "${TASK_REGION}")"
  TASK_TASK="$(aws emr list-instances --cluster-id "${TASK_CLUSTER_ID}" --instance-group-types TASK --instance-states RUNNING WAITING --query 'length(Instances)' --output text --region "${TASK_REGION}")"
  TASK_TOTAL="$((TASK_CORE + TASK_TASK))"
  echo "${TASK_TIMESTAMP},$((TASK_NOW - TASK_STARTED)),${TASK_CORE},${TASK_TASK},${TASK_TOTAL}" | tee -a "${TASK_OUTPUT}"
  sleep "${TASK_INTERVAL}"
done

TASK_DISTINCT_COUNTS="$(tail -n +2 "${TASK_OUTPUT}" | cut -d, -f5 | sort -u | wc -l | tr -d ' ')"
if [[ "${TASK_DISTINCT_COUNTS}" -gt 1 ]]; then
  echo "Observed an EMR worker-count change. Evidence: ${TASK_OUTPUT}"
else
  echo "No worker-count change was observed during this interval. Report this honestly and run a longer sustained workload."
fi
