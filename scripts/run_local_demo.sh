#!/usr/bin/env bash
set -euo pipefail

TASK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASK_PYTHON="${PYTHON:-python3}"
TASK_OUTPUT="${TASK_ROOT}/data/output"

mkdir -p "${TASK_OUTPUT}"
export PYTHONPATH="${TASK_ROOT}/src"

"${TASK_PYTHON}" -m clickstream_analytics.producer \
  "${TASK_ROOT}/tests/fixtures/clickstream.csv" \
  --rate 1000 \
  --no-sleep \
  --output "${TASK_OUTPUT}/replayed.jsonl"

"${TASK_PYTHON}" -m clickstream_analytics.speed \
  "${TASK_OUTPUT}/replayed.jsonl" \
  --output "${TASK_OUTPUT}/speed.json"

"${TASK_PYTHON}" "${TASK_ROOT}/jobs/sequential_baseline.py" \
  "${TASK_OUTPUT}/replayed.jsonl" \
  "${TASK_OUTPUT}/baseline.json"

"${TASK_PYTHON}" -m clickstream_analytics.serving \
  "${TASK_OUTPUT}/speed.json" \
  "${TASK_OUTPUT}/baseline.json" \
  --output "${TASK_OUTPUT}/serving.json"

echo "Local demo complete: ${TASK_OUTPUT}/serving.json"
