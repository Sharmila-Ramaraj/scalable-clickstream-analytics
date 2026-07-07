# Clickstream Analytics Dashboard

Interactive presentation layer for **Scalable Real-Time E-Commerce Clickstream Analytics** by Sharmila Ramaraj (X24244066).

The dashboard explains the verified project result through four straightforward views:

- a concise result summary for product 200;
- a numbered AWS processing flow from the producer to the serving merge;
- a three-stage session funnel showing the 66.67% cart-to-purchase drop-off;
- a simple batch chart comparing the 70-second reference run with the 58-second parallel run.

All displayed numbers come from the deterministic eight-event correctness replay or the separate 999,825-event EMR benchmark. The interface deliberately uses ordinary tables, progress bars, and labelled steps so the implementation remains clear and credible as student work.

## Run locally

Node.js 22.13 or newer is required.

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Validate

```bash
npm test
```

This creates and checks the static AWS production build, including the key analytical values, readable funnel labels, responsive layout, and absence of a sign-in screen.

## Public AWS version

[Open Scalable Real-Time Clickstream Analytics — X24244066](http://scalable-real-time-clickstream-analytics-x24244066.s3-website-us-east-1.amazonaws.com)

The AWS S3 website is public and does not require authentication. Its URL uses the project title and student ID.

To rebuild and publish it from the project root:

```bash
cd dashboard
npm ci
npm test
chmod +x ../scripts/deploy_dashboard_s3.sh
../scripts/deploy_dashboard_s3.sh
```

See the [complete from-scratch guide](../docs/from-scratch-implementation-guide.md) for the dataset, stream, batch, serving, benchmark, and deployment sequence.
