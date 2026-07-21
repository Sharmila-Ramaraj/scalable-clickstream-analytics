#!/usr/bin/env bash
set -euo pipefail

TASK_BUCKET_NAME="${1:-scalable-real-time-clickstream-analytics-x24244066}"
TASK_REGION="${AWS_REGION:-us-east-1}"
TASK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASK_ARCHIVE="${TASK_ROOT}/deploy/dashboard-static.zip"
TASK_TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TASK_TEMP_DIR}"' EXIT

if [[ ! -f "${TASK_ARCHIVE}" ]]; then
  echo "Missing prebuilt dashboard archive: ${TASK_ARCHIVE}" >&2
  exit 2
fi

if ! aws s3api head-bucket --bucket "${TASK_BUCKET_NAME}" 2>/dev/null; then
  echo "The existing dashboard bucket is unavailable: ${TASK_BUCKET_NAME}" >&2
  exit 3
fi

unzip -q "${TASK_ARCHIVE}" -d "${TASK_TEMP_DIR}"

echo "Uploading the prebuilt student dashboard"
aws s3 sync "${TASK_TEMP_DIR}" "s3://${TASK_BUCKET_NAME}" \
  --delete \
  --region "${TASK_REGION}"

echo "Deployment complete"
echo "http://${TASK_BUCKET_NAME}.s3-website-${TASK_REGION}.amazonaws.com"
