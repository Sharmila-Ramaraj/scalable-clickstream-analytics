# StreamCart 3D Clickstream Dashboard

Interactive presentation layer for **Scalable Real-Time E-Commerce Clickstream Analytics** by Sharmila Ramaraj (X24244066).

The dashboard explains the verified project result through four connected views:

- a pauseable 3D trend scene for product 200;
- a switchable AWS flow from producer to Kinesis, Lambda, and DynamoDB;
- a three-stage session funnel showing the 66.67% cart-to-purchase drop-off;
- a 3D batch chart comparing the 70-second reference run with the 58-second parallel run.

All displayed numbers come from the deterministic eight-event correctness replay or the separate 999,825-event EMR benchmark. Animation is used only for presentation and does not change the data.

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

This builds the production worker and checks the rendered result, key analytical values, interactions, responsive layout, and reduced-motion support.
