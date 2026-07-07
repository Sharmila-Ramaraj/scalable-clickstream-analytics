"use client";

import { useState } from "react";

const products = [
  { id: "200", views: 2, carts: 1, purchases: 0, score: 5, baseline: 2.5, lift: 2.0, status: "Unusually trending" },
  { id: "100", views: 2, carts: 2, purchases: 1, score: 13, baseline: 13.0, lift: 1.0, status: "Normal activity" },
];

const services = [
  ["Python producer", "Validates and replays the REES46 CSV"],
  ["Amazon Kinesis", "Receives the session-partitioned event stream"],
  ["AWS Lambda", "Updates recent product counters"],
  ["DynamoDB", "Stores one-minute speed-layer buckets"],
  ["Amazon S3 + EMR", "Stores history and computes PySpark baselines"],
  ["Serving merge", "Compares current activity with historical norms"],
];

function MetricCard({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <article className="metric-card">
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{note}</span>
    </article>
  );
}

export default function Home() {
  const [refreshed, setRefreshed] = useState("19:39 UTC");

  return (
    <main>
      <header className="site-header">
        <div className="header-inner">
          <div>
            <p className="course-label">SCALABLE CLOUD PROGRAMMING · AWS ACADEMY LEARNER LAB</p>
            <h1>Scalable Real-Time E-Commerce Clickstream Analytics</h1>
            <p className="student-line">Sharmila Ramaraj · X24244066</p>
          </div>
          <div className="header-meta">
            <span>Region: us-east-1</span>
            <span>Window: 5 minutes</span>
            <button onClick={() => setRefreshed("just now")}>Refresh view</button>
          </div>
        </div>
      </header>

      <div className="page-shell">
        <section className="summary-card" aria-labelledby="answer-title">
          <div>
            <p className="section-label">REAL-TIME ANALYTICAL ANSWER</p>
            <h2 id="answer-title">Product 200 is unusually trending</h2>
            <p>
              Its current trend score is <strong>5</strong>, compared with a historical five-minute average of <strong>2.5</strong>.
              This gives an activity lift of <strong>2.0×</strong>, which meets the project threshold.
            </p>
          </div>
          <aside className="decision-box">
            <b>Recommended business response</b>
            <p>Check product stock and promotion activity. Investigate purchase friction because the largest session loss occurs after cart.</p>
          </aside>
        </section>

        <div className="status-row">
          <span className="status-dot" /> Verified correctness replay
          <span>8 events</span>
          <span>Last displayed refresh: {refreshed}</span>
        </div>

        <section className="metrics-grid" aria-label="Verified project metrics">
          <MetricCard label="Events in current window" value="8" note="Deterministic test stream" />
          <MetricCard label="View sessions" value="4" note="Three reached cart" />
          <MetricCard label="Unusual products" value="1 of 2" note="Threshold: activity lift ≥ 2.0×" />
          <MetricCard label="PySpark speedup" value="1.207×" note="Eight partitions compared with one" />
        </section>

        <section className="panel" id="products">
          <div className="panel-heading">
            <div><p className="section-label">SPEED + BATCH SERVING VIEW</p><h2>Product activity compared with history</h2></div>
            <span className="verified-tag">Verified result</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Product</th><th>Views</th><th>Carts</th><th>Purchases</th><th>Current score</th><th>Historical average</th><th>Lift</th><th>Result</th></tr></thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product.id}>
                    <td><b>#{product.id}</b></td>
                    <td>{product.views}</td><td>{product.carts}</td><td>{product.purchases}</td>
                    <td>{product.score}</td><td>{product.baseline.toFixed(1)}</td><td><b>{product.lift.toFixed(1)}×</b></td>
                    <td><span className={product.lift >= 2 ? "result unusual" : "result normal"}>{product.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="formula-note">Trend score = views + (3 × carts) + (5 × purchases). A product is unusual when current score is at least twice its historical five-minute average.</p>
        </section>

        <div className="two-column">
          <section className="panel" id="funnel">
            <div className="panel-heading"><div><p className="section-label">SESSION FUNNEL</p><h2>Where users drop off</h2></div></div>
            <div className="funnel-row"><div><b>Viewed</b><span>4 sessions</span></div><div className="progress"><i style={{ width: "100%" }} /></div><strong>100%</strong></div>
            <p className="drop-text">25% view-to-cart drop-off</p>
            <div className="funnel-row"><div><b>Added to cart</b><span>3 sessions</span></div><div className="progress"><i style={{ width: "75%" }} /></div><strong>75%</strong></div>
            <p className="drop-text warning">66.67% cart-to-purchase drop-off</p>
            <div className="funnel-row"><div><b>Purchased</b><span>1 session</span></div><div className="progress"><i style={{ width: "25%" }} /></div><strong>25%</strong></div>
            <div className="finding"><b>Main finding:</b> cart-to-purchase is the larger loss and should be investigated first.</div>
          </section>

          <section className="panel" id="performance">
            <div className="panel-heading"><div><p className="section-label">PYSPARK ON AMAZON EMR</p><h2>Batch processing benchmark</h2></div></div>
            <p className="supporting-copy">Both runs used the same two-worker cluster and the same 999,825-event input.</p>
            <div className="bar-row"><span>1 partition</span><div><i style={{ width: "100%" }} /></div><b>70 s</b></div>
            <div className="bar-row parallel"><span>8 partitions</span><div><i style={{ width: "82.86%" }} /></div><b>58 s</b></div>
            <dl className="benchmark-summary"><div><dt>Time saved</dt><dd>12 seconds</dd></div><div><dt>Duration reduction</dt><dd>17.1%</dd></div><div><dt>Speedup</dt><dd>1.207×</dd></div></dl>
            <p className="limitation"><b>Scope:</b> this proves partition-level parallelism on the same cluster. It does not prove worker-count scaling.</p>
          </section>
        </div>

        <section className="panel" id="architecture">
          <div className="panel-heading"><div><p className="section-label">IMPLEMENTED AWS LAMBDA ARCHITECTURE</p><h2>How the result is produced</h2></div></div>
          <div className="pipeline" aria-label="AWS processing pipeline">
            {services.map(([name, detail], index) => (
              <div className="pipeline-step" key={name}>
                <span>{index + 1}</span><div><b>{name}</b><small>{detail}</small></div>
              </div>
            ))}
          </div>
          <div className="architecture-note">
            <p><b>Speed path:</b> Kinesis → Lambda → DynamoDB provides recent activity.</p>
            <p><b>Batch path:</b> S3 → EMR PySpark provides historical five-minute averages.</p>
            <p><b>Serving layer:</b> the two views are merged to calculate product activity lift and funnel drop-off.</p>
          </div>
        </section>

        <footer>
          <p>Public REES46 electronics events · AWS Academy Learner Lab · Individual student implementation</p>
          <p>This dashboard presents verified assessment results and is not a production monitoring system.</p>
        </footer>
      </div>
    </main>
  );
}
