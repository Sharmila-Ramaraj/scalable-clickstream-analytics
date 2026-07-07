#!/usr/bin/env bash
set -euo pipefail

TASK_BUCKET_NAME="${1:-scalable-real-time-clickstream-analytics-x24244066}"
TASK_REGION="${AWS_REGION:-us-east-1}"
TASK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASK_DASHBOARD_DIR="${TASK_ROOT}/dashboard"

cd "${TASK_DASHBOARD_DIR}"

echo "[1/5] Building the static dashboard"
npm run build:aws

echo "[2/5] Creating or reusing the S3 bucket"
if ! aws s3api head-bucket --bucket "${TASK_BUCKET_NAME}" 2>/dev/null; then
  if [[ "${TASK_REGION}" == "us-east-1" ]]; then
    aws s3api create-bucket \
      --bucket "${TASK_BUCKET_NAME}" \
      --region "${TASK_REGION}" >/dev/null
  else
    aws s3api create-bucket \
      --bucket "${TASK_BUCKET_NAME}" \
      --create-bucket-configuration "LocationConstraint=${TASK_REGION}" \
      --region "${TASK_REGION}" >/dev/null
  fi
fi

echo "[3/5] Enabling static website access"
aws s3api put-public-access-block \
  --bucket "${TASK_BUCKET_NAME}" \
  --public-access-block-configuration \
    'BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false' \
  --region "${TASK_REGION}"

TASK_PUBLIC_POLICY="{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"PublicReadForWebsite\",\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"s3:GetObject\",\"Resource\":\"arn:aws:s3:::${TASK_BUCKET_NAME}/*\"}]}"
aws s3api put-bucket-policy \
  --bucket "${TASK_BUCKET_NAME}" \
  --policy "${TASK_PUBLIC_POLICY}" \
  --region "${TASK_REGION}"

aws s3 website "s3://${TASK_BUCKET_NAME}" \
  --index-document index.html \
  --error-document 404.html \
  --region "${TASK_REGION}"

echo "[4/5] Uploading the production files"
aws s3 sync out "s3://${TASK_BUCKET_NAME}" \
  --delete \
  --region "${TASK_REGION}"

echo "[5/5] Deployment complete"
echo "http://${TASK_BUCKET_NAME}.s3-website-${TASK_REGION}.amazonaws.com"
