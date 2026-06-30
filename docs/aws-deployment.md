# AWS Academy Learner Lab deployment

This guide intentionally separates code that can be verified locally from steps that require an active Learner Lab session. Use the region, account number, `LabRole` ARN, and service permissions shown in your own lab.

## 1. Start the lab and record configuration

Record these values in a private local note; do not commit temporary credentials:

- AWS region
- account ID
- `LabRole` ARN
- lab budget before deployment

Configure the AWS CLI using the temporary values supplied by the lab and confirm access with `aws sts get-caller-identity`.

## 2. Create the core resources

From the project root:

```bash
aws cloudformation deploy \
  --template-file infrastructure.yaml \
  --stack-name clickstream-analytics \
  --parameter-overrides ProjectName=clickstream-analytics \
  --region YOUR_LAB_REGION

aws cloudformation describe-stacks \
  --stack-name clickstream-analytics \
  --query 'Stacks[0].Outputs' \
  --region YOUR_LAB_REGION
```

This creates one Kinesis shard, two private encrypted S3 buckets, and an on-demand DynamoDB table. The S3 buckets have retention safeguards in the template.

## 3. Preserve the raw stream

In the AWS console, create an Amazon Data Firehose delivery stream:

1. Source: the `clickstream-analytics-events` Kinesis stream.
2. Destination: the raw S3 bucket from the stack output.
3. Role: the Learner Lab `LabRole`, if permitted.
4. Buffering: use the smallest lab-supported interval for demonstration.
5. Prefix: `raw/events/` and error prefix `raw/errors/`.

The producer terminates every Kinesis record with a newline, so buffered S3 objects remain valid newline-delimited JSON for Spark. Confirm that replaying data creates S3 objects and that their record count matches the accepted producer count. If Data Firehose is not permitted in the lab, use a second Kinesis consumer that writes buffered JSONL objects to S3 and document this substitution.

## 4. Deploy the speed Lambda

The handler depends only on Python's standard library and the `boto3` library already available in the Lambda Python runtime:

```bash
mkdir -p build/lambda
cp jobs/speed_lambda.py build/lambda/
cd build/lambda
zip speed-lambda.zip speed_lambda.py
cd ../..

aws lambda create-function \
  --function-name clickstream-speed \
  --runtime python3.12 \
  --handler speed_lambda.lambda_handler \
  --role YOUR_LAB_ROLE_ARN \
  --zip-file fileb://build/lambda/speed-lambda.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment 'Variables={METRICS_TABLE=clickstream-analytics-speed-metrics,RETENTION_HOURS=48}' \
  --region YOUR_LAB_REGION
```

Create a Kinesis event-source mapping with a small batching window and partial-batch reporting:

```bash
aws lambda create-event-source-mapping \
  --function-name clickstream-speed \
  --event-source-arn YOUR_KINESIS_STREAM_ARN \
  --starting-position LATEST \
  --batch-size 100 \
  --maximum-batching-window-in-seconds 1 \
  --function-response-types ReportBatchItemFailures \
  --region YOUR_LAB_REGION
```

The handler returns failed Kinesis sequence numbers. AWS only uses that response when `ReportBatchItemFailures` is enabled on the mapping; see the [official Lambda Kinesis failure-reporting guide](https://docs.aws.amazon.com/lambda/latest/dg/services-kinesis-batchfailurereporting.html).

## 5. Run the producer

Install the project with AWS support and replay a bounded subset first:

```bash
python3 -m pip install -e '.[aws]'

clickstream-replay /path/to/2019-Oct.csv.gz \
  --rate 100 \
  --limit 10000 \
  --kinesis-stream clickstream-analytics-events \
  --region YOUR_LAB_REGION
```

Verify:

- producer accepted count;
- Kinesis incoming records/bytes;
- Lambda invocations, errors, duration and throttles;
- DynamoDB rows with `WINDOW#<minute>` keys;
- raw S3 objects.

Increase the rate only after the small run is correct.

## 6. Run the PySpark batch layer on EMR

Upload the job to the analytics bucket:

```bash
aws s3 cp jobs/batch_baseline.py \
  s3://YOUR_ANALYTICS_BUCKET/jobs/batch_baseline.py \
  --region YOUR_LAB_REGION
```

Create an EMR-on-EC2 cluster with Spark, the Learner Lab roles permitted by the environment, and a lab-safe managed-scaling range. For initial testing, use one primary and the smallest supported worker configuration. Submit:

```bash
spark-submit s3://YOUR_ANALYTICS_BUCKET/jobs/batch_baseline.py \
  s3://YOUR_RAW_BUCKET/raw/events/ \
  s3://YOUR_ANALYTICS_BUCKET/batch/product-baselines/ \
  --partitions 8
```

EMR managed scaling is bounded by minimum and maximum capacity units and only scales core/task capacity, not the primary node. Confirm the actual region/release support and record the policy used; see the [official EMR managed-scaling documentation](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-managed-scaling.html).

## 7. Benchmark safely

Use the same input object set for every comparison. Record:

- input event count and bytes;
- Spark partitions and worker nodes;
- start/end timestamps and duration;
- Kinesis rate, iterator age and shard count;
- Lambda p50/p95 duration and errors;
- end-to-end event latency from the speed metrics;
- scaling event timestamps.

Run a low, medium and high ingestion rate, and run batch processing with one, two and four workers if the lab budget permits. Repeat configurations three times and report the median plus variability.

## 8. End each lab session

Terminate the EMR cluster immediately after capturing results. Stop the Learner Lab when finished. The CloudFormation template deliberately retains S3 data; delete retained buckets only after downloading evidence and confirming that the data is no longer needed.
