#!/usr/bin/env bash
set -euo pipefail

TASK_PROJECT_NAME="scp-clickstream"
TASK_REGION="${AWS_REGION:-us-east-1}"
TASK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASK_RUN_DIR="${TASK_ROOT}/run"

mkdir -p "${TASK_RUN_DIR}" "${TASK_ROOT}/build/lambda"
cd "${TASK_ROOT}"

echo "[1/8] Verifying the active Learner Lab identity"
aws sts get-caller-identity --region "${TASK_REGION}"

echo "[2/8] Creating Kinesis, S3 and DynamoDB resources"
aws cloudformation deploy \
  --template-file infrastructure.yaml \
  --stack-name "${TASK_PROJECT_NAME}" \
  --parameter-overrides ProjectName="${TASK_PROJECT_NAME}" \
  --region "${TASK_REGION}"

TASK_STREAM_NAME="$(aws cloudformation describe-stacks \
  --stack-name "${TASK_PROJECT_NAME}" \
  --query "Stacks[0].Outputs[?OutputKey=='StreamName'].OutputValue" \
  --output text \
  --region "${TASK_REGION}")"
TASK_RAW_BUCKET="$(aws cloudformation describe-stacks \
  --stack-name "${TASK_PROJECT_NAME}" \
  --query "Stacks[0].Outputs[?OutputKey=='RawBucketName'].OutputValue" \
  --output text \
  --region "${TASK_REGION}")"
TASK_ANALYTICS_BUCKET="$(aws cloudformation describe-stacks \
  --stack-name "${TASK_PROJECT_NAME}" \
  --query "Stacks[0].Outputs[?OutputKey=='AnalyticsBucketName'].OutputValue" \
  --output text \
  --region "${TASK_REGION}")"
TASK_METRICS_TABLE="$(aws cloudformation describe-stacks \
  --stack-name "${TASK_PROJECT_NAME}" \
  --query "Stacks[0].Outputs[?OutputKey=='MetricsTableName'].OutputValue" \
  --output text \
  --region "${TASK_REGION}")"
TASK_STREAM_ARN="$(aws kinesis describe-stream-summary \
  --stream-name "${TASK_STREAM_NAME}" \
  --query StreamDescriptionSummary.StreamARN \
  --output text \
  --region "${TASK_REGION}")"
TASK_LAB_ROLE_ARN="$(aws iam get-role \
  --role-name LabRole \
  --query Role.Arn \
  --output text \
  --region "${TASK_REGION}")"

echo "[3/8] Packaging and deploying the speed-layer Lambda"
cp jobs/speed_lambda.py build/lambda/speed_lambda.py
cd build/lambda
zip -q -FS speed-lambda.zip speed_lambda.py
cd "${TASK_ROOT}"

if aws lambda get-function \
  --function-name "${TASK_PROJECT_NAME}-speed" \
  --region "${TASK_REGION}" >/dev/null 2>&1; then
  aws lambda update-function-code \
    --function-name "${TASK_PROJECT_NAME}-speed" \
    --zip-file fileb://build/lambda/speed-lambda.zip \
    --region "${TASK_REGION}" >/dev/null
  aws lambda wait function-updated-v2 \
    --function-name "${TASK_PROJECT_NAME}-speed" \
    --region "${TASK_REGION}"
  aws lambda update-function-configuration \
    --function-name "${TASK_PROJECT_NAME}-speed" \
    --role "${TASK_LAB_ROLE_ARN}" \
    --runtime python3.12 \
    --handler speed_lambda.lambda_handler \
    --timeout 30 \
    --memory-size 256 \
    --environment "Variables={METRICS_TABLE=${TASK_METRICS_TABLE},RETENTION_HOURS=48}" \
    --region "${TASK_REGION}" >/dev/null
else
  aws lambda create-function \
    --function-name "${TASK_PROJECT_NAME}-speed" \
    --runtime python3.12 \
    --handler speed_lambda.lambda_handler \
    --role "${TASK_LAB_ROLE_ARN}" \
    --zip-file fileb://build/lambda/speed-lambda.zip \
    --timeout 30 \
    --memory-size 256 \
    --environment "Variables={METRICS_TABLE=${TASK_METRICS_TABLE},RETENTION_HOURS=48}" \
    --region "${TASK_REGION}" >/dev/null
fi

aws lambda wait function-active-v2 \
  --function-name "${TASK_PROJECT_NAME}-speed" \
  --region "${TASK_REGION}"

TASK_MAPPING_UUID="$(aws lambda list-event-source-mappings \
  --function-name "${TASK_PROJECT_NAME}-speed" \
  --event-source-arn "${TASK_STREAM_ARN}" \
  --query 'EventSourceMappings[0].UUID' \
  --output text \
  --region "${TASK_REGION}")"

if [[ "${TASK_MAPPING_UUID}" == "None" ]]; then
  TASK_MAPPING_UUID="$(aws lambda create-event-source-mapping \
    --function-name "${TASK_PROJECT_NAME}-speed" \
    --event-source-arn "${TASK_STREAM_ARN}" \
    --starting-position LATEST \
    --batch-size 100 \
    --maximum-batching-window-in-seconds 1 \
    --function-response-types ReportBatchItemFailures \
    --query UUID \
    --output text \
    --region "${TASK_REGION}")"
fi

echo "Waiting for the Kinesis trigger to become enabled"
for _ in {1..30}; do
  TASK_MAPPING_STATE="$(aws lambda get-event-source-mapping \
    --uuid "${TASK_MAPPING_UUID}" \
    --query State \
    --output text \
    --region "${TASK_REGION}")"
  if [[ "${TASK_MAPPING_STATE}" == "Enabled" ]]; then
    break
  fi
  sleep 2
done
if [[ "${TASK_MAPPING_STATE}" != "Enabled" ]]; then
  echo "Kinesis trigger did not become enabled; current state: ${TASK_MAPPING_STATE}" >&2
  exit 1
fi

echo "[4/8] Producing the local batch and serving views"
export PYTHONPATH="${TASK_ROOT}/src"
python3 -m clickstream_analytics.producer \
  tests/fixtures/clickstream.csv \
  --rate 1000 \
  --no-sleep \
  --output "${TASK_RUN_DIR}/replayed.jsonl"
python3 jobs/sequential_baseline.py \
  "${TASK_RUN_DIR}/replayed.jsonl" \
  "${TASK_RUN_DIR}/baseline.json"
python3 -m clickstream_analytics.speed \
  "${TASK_RUN_DIR}/replayed.jsonl" \
  --output "${TASK_RUN_DIR}/speed.json"
python3 -m clickstream_analytics.serving \
  "${TASK_RUN_DIR}/speed.json" \
  "${TASK_RUN_DIR}/baseline.json" \
  --output "${TASK_RUN_DIR}/serving.json"

echo "[5/8] Uploading reproducible batch evidence to S3"
aws s3 cp "${TASK_RUN_DIR}/replayed.jsonl" \
  "s3://${TASK_RAW_BUCKET}/raw/events/demo.jsonl" \
  --region "${TASK_REGION}" >/dev/null
aws s3 cp "${TASK_RUN_DIR}/baseline.json" \
  "s3://${TASK_ANALYTICS_BUCKET}/batch/baseline.json" \
  --region "${TASK_REGION}" >/dev/null
aws s3 cp "${TASK_RUN_DIR}/speed.json" \
  "s3://${TASK_ANALYTICS_BUCKET}/speed/snapshot.json" \
  --region "${TASK_REGION}" >/dev/null
aws s3 cp "${TASK_RUN_DIR}/serving.json" \
  "s3://${TASK_ANALYTICS_BUCKET}/serving/merged-view.json" \
  --region "${TASK_REGION}" >/dev/null
aws s3 cp jobs/batch_baseline.py \
  "s3://${TASK_ANALYTICS_BUCKET}/jobs/batch_baseline.py" \
  --region "${TASK_REGION}" >/dev/null

echo "[6/8] Sending the demonstration stream to Kinesis"
python3 -m clickstream_analytics.producer \
  tests/fixtures/clickstream.csv \
  --rate 4 \
  --kinesis-stream "${TASK_STREAM_NAME}" \
  --region "${TASK_REGION}"

echo "[7/8] Waiting briefly for Lambda and checking DynamoDB"
sleep 8
aws dynamodb scan \
  --table-name "${TASK_METRICS_TABLE}" \
  --select COUNT \
  --region "${TASK_REGION}"

echo "[8/8] Deployment complete"
cat <<OUTPUT

Region:           ${TASK_REGION}
Kinesis stream:  ${TASK_STREAM_NAME}
Raw S3 bucket:    ${TASK_RAW_BUCKET}
Analytics bucket: ${TASK_ANALYTICS_BUCKET}
DynamoDB table:   ${TASK_METRICS_TABLE}
Lambda function:  ${TASK_PROJECT_NAME}-speed

Merged serving result:
${TASK_RUN_DIR}/serving.json

Display it with:
cat ${TASK_RUN_DIR}/serving.json
OUTPUT
