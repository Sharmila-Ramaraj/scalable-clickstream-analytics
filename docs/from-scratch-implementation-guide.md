# From-scratch implementation guide

## Project outcome

This project answers one operational e-commerce question:

> Which products are unusually active in the latest five-minute window, and is the larger session loss from view to cart or from cart to purchase?

The system combines recent stream aggregates with historical PySpark baselines. The verified demonstration identifies product 200 as unusually trending at a 2.0x lift and identifies cart-to-purchase as the larger funnel loss at 66.67%.

Live AWS dashboard: [Scalable Real-Time Clickstream Analytics — X24244066](http://scalable-real-time-clickstream-analytics-x24244066.s3-website-us-east-1.amazonaws.com)

## 1. Architecture

1. A Python producer reads a public REES46 e-commerce CSV file, validates each row, rebases event times for a live replay, and partitions Kinesis records by session ID.
2. Amazon Kinesis Data Streams accepts the events.
3. The speed path invokes AWS Lambda, which updates one-minute product and health aggregates in DynamoDB.
4. The history path preserves canonical events in Amazon S3.
5. PySpark on Amazon EMR calculates historical five-minute product baselines and funnel totals from S3.
6. The serving code merges the current and historical views and computes activity lift.
7. A static Next.js dashboard presents product trends, funnel loss, AWS flow, and benchmark evidence. The static production output is hosted as a public Amazon S3 website.

The trend score is:

```text
views + (3 × carts) + (5 × purchases)
```

Activity lift is `current trend score / historical five-minute mean`. A product is flagged as unusual when lift is at least 2.0x.

## 2. Prerequisites

- Python 3.11 or newer
- Node.js 22.13 or newer
- An active AWS Academy Learner Lab session
- AWS CLI credentials inherited from the Learner Lab console or CloudShell
- AWS region `us-east-1` for the verified deployment
- Git only if source control is required

Never copy Learner Lab keys into source files, screenshots, reports, or GitHub. Start the lab, use the **AWS** launch button, and work in the console or CloudShell session it opens.

## 3. Prepare the project locally

From the project root:

```bash
python3 -m pip install -e '.[test,aws]'
export PYTHONPATH="$PWD/src"
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The seven deterministic Python tests verify parsing, replay, window calculations, the serving merge, and the sequential baseline.

## 4. Download and normalise the public dataset

Download the REES46 electronics events file:

```bash
mkdir -p data/raw run
curl -L --fail --retry 3 \
  -o data/raw/electronics-events.csv.gz \
  https://data.rees46.com/datasets/electronics-events/electronics-events.csv.gz
gzip -dc data/raw/electronics-events.csv.gz | head -3
```

Create a bounded canonical replay file:

```bash
time python3 -m clickstream_analytics.producer \
  data/raw/electronics-events.csv.gz \
  --limit 200000 \
  --rate 100000 \
  --no-sleep \
  --output run/real-200k.jsonl
```

Verified result:

- 200,000 source rows inspected
- 199,965 accepted events
- 35 rows rejected because `user_session` was missing
- about 58 MB of canonical JSONL
- 16.804 seconds to normalise on the measured environment

Rows without a session ID are rejected because their view, cart, and purchase actions cannot be attributed to one customer journey.

## 5. Verify the complete pipeline locally

Run the deterministic eight-event fixture:

```bash
chmod +x scripts/run_local_demo.sh
./scripts/run_local_demo.sh
cat data/output/serving.json
```

The expected answer is:

- product 200: score 5, baseline 2.5, lift 2.0x, unusually trending;
- product 100: score 13, baseline 13, lift 1.0x, normal;
- view-to-cart drop-off: 25%;
- cart-to-purchase drop-off: 66.67%.

The small fixture is used for correctness. It is deliberately separate from the large performance dataset.

## 6. Deploy Kinesis, Lambda, DynamoDB, and S3

Open AWS CloudShell from the active Learner Lab in `us-east-1`. Upload the project ZIP, extract it, enter the project directory, and run:

```bash
chmod +x scripts/cloudshell_deploy.sh
./scripts/cloudshell_deploy.sh
```

The deployment script:

1. verifies the active AWS identity;
2. deploys the CloudFormation stack `scp-clickstream`;
3. creates the Kinesis stream, two private S3 buckets, and on-demand DynamoDB table;
4. packages and deploys the Python 3.12 speed Lambda;
5. creates and waits for the Kinesis event-source mapping;
6. generates deterministic batch, speed, and serving evidence;
7. uploads evidence and the Spark job to S3;
8. sends the eight-event replay to Kinesis.

The verified resource names are:

```text
Kinesis:  scp-clickstream-events
DynamoDB: scp-clickstream-speed-metrics
Lambda:   scp-clickstream-speed
```

The two data-bucket names include the temporary Learner Lab account number, so retrieve them from the CloudFormation output instead of hard-coding them.

Check the trigger and result:

```bash
aws lambda list-event-source-mappings \
  --function-name scp-clickstream-speed \
  --query 'EventSourceMappings[0].[State,LastProcessingResult]' \
  --output table \
  --region us-east-1

aws dynamodb scan \
  --table-name scp-clickstream-speed-metrics \
  --select COUNT \
  --region us-east-1
```

If the trigger was still activating during the first replay, send the fixture again after its state becomes `Enabled`. The verified table count is three rows: two product aggregates and one processing-health row.

## 7. Prepare and run the EMR batch benchmark

Upload the 199,965-event canonical subset to the raw S3 bucket. Five S3-side copies form the verified input of 999,825 events, approximately 290 MB. Upload `jobs/batch_baseline.py` to the analytics bucket.

The measured cluster used:

- Amazon EMR 7.13.0 and Spark 3.5.6;
- one primary, one core worker, and one task worker at launch;
- managed scaling from two to four workers, with at most one core worker;
- automatic termination after 20 idle minutes.

Submit the same Spark program twice against exactly the same input: first with `--partitions 1`, then with `--partitions 8`.

```bash
spark-submit s3://YOUR_ANALYTICS_BUCKET/jobs/batch_baseline.py \
  s3://YOUR_RAW_BUCKET/raw/benchmark/ \
  s3://YOUR_ANALYTICS_BUCKET/batch/product-baselines-p1/ \
  --partitions 1

spark-submit s3://YOUR_ANALYTICS_BUCKET/jobs/batch_baseline.py \
  s3://YOUR_RAW_BUCKET/raw/benchmark/ \
  s3://YOUR_ANALYTICS_BUCKET/batch/product-baselines-p8/ \
  --partitions 8
```

Verified measurements:

| Configuration | Partitions | Duration | Speedup |
|---|---:|---:|---:|
| Sequential reference | 1 | 70 s | 1.000x |
| Parallel execution | 8 | 58 s | 1.207x |

The eight-partition run saved 12 seconds, a 17.1% duration reduction. This is a controlled partition-parallelism comparison on the same two-worker cluster; it is not evidence of controlled worker-count scaling. The short jobs also did not sustain enough demand to demonstrate a managed-scaling event.

Verify that both output locations contain `_SUCCESS`, Parquet parts, and the consolidated JSON result before terminating the cluster.

## 8. Build and verify the dashboard

```bash
cd dashboard
npm ci
npm test
npm run build:aws
```

The production files are written to `dashboard/out`. The automated check validates the key analytical values, the three readable funnel stages, mobile styling, and the absence of a sign-in screen.

For local visual inspection:

```bash
npx serve out -l 4173
```

Open `http://localhost:4173` and verify desktop and narrow mobile widths before publishing.

## 9. Publish the title-based AWS website

The deployment uses the bucket name as the human-readable website URL:

```text
scalable-real-time-clickstream-analytics-x24244066
```

From the dashboard directory, run:

```bash
chmod +x ../scripts/deploy_dashboard_s3.sh
../scripts/deploy_dashboard_s3.sh
```

The script builds the static dashboard, creates or updates the S3 bucket, configures website hosting, uploads `out`, and grants public read access only to website objects.

Public URL:

```text
http://scalable-real-time-clickstream-analytics-x24244066.s3-website-us-east-1.amazonaws.com
```

S3 website endpoints use HTTP. The site is public and does not require an application, AWS, or GitHub login. For production outside an assessment lab, place CloudFront and HTTPS in front of the private S3 origin instead of using the public website endpoint.

## 10. Evidence and demonstration checklist

Capture evidence only after checking that it exposes no temporary credentials or account identifiers:

- CloudFormation outputs and active resources;
- Kinesis-to-Lambda mapping state `Enabled`;
- DynamoDB count of three after the deterministic replay;
- merged serving JSON with product 200 at 2.0x and funnel percentages;
- EMR step timings of 70 and 58 seconds;
- `_SUCCESS` and batch output objects in S3;
- corrected public dashboard and its AWS URL;
- automated Python and dashboard test results.

Recommended video sequence:

1. State the question and architecture.
2. Open the public AWS dashboard and point out the AWS URL and absence of login.
3. Explain product 200's current score, baseline, and 2.0x lift.
4. Explain the readable funnel and why 66.67% is the primary friction point.
5. Show the 70-second versus 58-second EMR evidence and state the limitation accurately.
6. Show the AWS flow and the Kinesis/Lambda/DynamoDB evidence.
7. Close with limitations and proposed future work.

## 11. Limitations and cleanup

- Kinesis retries can cause duplicate DynamoDB increments because the demonstration counters do not yet use idempotency keys.
- The measured benchmark changes Spark partitions, not worker count.
- Managed scaling was configured but no scale-out was observed during the short jobs.
- The eight-event stream proves correctness, not sustained high-rate Kinesis throughput.
- A production system should add authentication for private business analytics and use CloudFront HTTPS.

Terminate EMR immediately after collecting evidence. Stop the Learner Lab when finished. Keep the two private evidence buckets until report and video assets are downloaded. The public dashboard bucket can be emptied and deleted after grading if it is no longer needed.
