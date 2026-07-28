"use client";

import { useState } from "react";

type Layer = "overview" | "speed" | "batch" | "serving";

const products = [
  { id: "200", views: 2, carts: 1, purchases: 0, score: 5, baseline: 2.5, lift: 2.0, status: "Unusually trending" },
  { id: "100", views: 2, carts: 2, purchases: 1, score: 13, baseline: 13.0, lift: 1.0, status: "Normal activity" },
];

const layerTabs: { id: Layer; label: string; description: string }[] = [
  { id: "overview", label: "Overview", description: "Current answer" },
  { id: "speed", label: "Speed Layer", description: "Recent activity" },
  { id: "batch", label: "Batch Layer", description: "Historical view" },
  { id: "serving", label: "Serving Layer", description: "Merged result" },
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

function ProductTable({ includeBaseline = true }: { includeBaseline?: boolean }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Product</th><th>Views</th><th>Carts</th><th>Purchases</th><th>Current score</th>
            {includeBaseline && <><th>Historical average</th><th>Lift</th><th>Result</th></>}
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr key={product.id}>
              <td><b>#{product.id}</b></td>
              <td>{product.views}</td><td>{product.carts}</td><td>{product.purchases}</td><td>{product.score}</td>
              {includeBaseline && <>
                <td>{product.baseline.toFixed(1)}</td><td><b>{product.lift.toFixed(1)}×</b></td>
                <td><span className={product.lift >= 2 ? "result unusual" : "result normal"}>{product.status}</span></td>
              </>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FunnelPanel() {
  return (
    <section className="panel">
      <div className="panel-heading"><div><p className="section-label">SESSION FUNNEL</p><h2>Where users drop off</h2></div></div>
      <div className="funnel-row"><div><b>Viewed</b><span>4 sessions</span></div><div className="progress"><i style={{ width: "100%" }} /></div><strong>100%</strong></div>
      <p className="drop-text">25% view-to-cart drop-off</p>
      <div className="funnel-row"><div><b>Added to cart</b><span>3 sessions</span></div><div className="progress"><i style={{ width: "75%" }} /></div><strong>75%</strong></div>
      <p className="drop-text warning">66.67% cart-to-purchase drop-off</p>
      <div className="funnel-row"><div><b>Purchased</b><span>1 session</span></div><div className="progress"><i style={{ width: "25%" }} /></div><strong>25%</strong></div>
      <div className="finding"><b>Main finding:</b> cart-to-purchase is the larger loss and should be investigated first.</div>
    </section>
  );
}

function BenchmarkPanel() {
  return (
    <section className="panel">
      <div className="panel-heading"><div><p className="section-label">PYSPARK ON AMAZON EMR</p><h2>Batch processing benchmark</h2></div></div>
      <p className="supporting-copy">Both runs used the same two-worker cluster and the same 999,825-event input.</p>
      <div className="bar-row"><span>1 partition</span><div><i style={{ width: "100%" }} /></div><b>70 s</b></div>
      <div className="bar-row parallel"><span>8 partitions</span><div><i style={{ width: "82.86%" }} /></div><b>58 s</b></div>
      <dl className="benchmark-summary"><div><dt>Time saved</dt><dd>12 seconds</dd></div><div><dt>Duration reduction</dt><dd>17.1%</dd></div><div><dt>Speedup</dt><dd>1.207×</dd></div></dl>
      <p className="limitation"><b>Scope:</b> this demonstrates partition-level parallelism on the same cluster. It does not claim worker-count scaling.</p>
    </section>
  );
}

export default function Home() {
  const [activeLayer, setActiveLayer] = useState<Layer>("overview");
  const [refreshed, setRefreshed] = useState("19:39 UTC");

  return (
    <main>
      <header className="site-header">
        <div className="header-inner">
          <h1>Scalable Real-Time E-Commerce Clickstream Analytics</h1>
          <div className="header-meta">
            <span>Region: us-east-1</span>
            <span>Window: 5 minutes</span>
            <button onClick={() => setRefreshed("just now")}>Refresh view</button>
          </div>
        </div>

        <nav className="layer-nav" aria-label="Analytics layers" role="tablist">
          {layerTabs.map((tab) => (
            <button
              key={tab.id}
              className={activeLayer === tab.id ? "active" : ""}
              onClick={() => setActiveLayer(tab.id)}
              id={`tab-${tab.id}`}
              role="tab"
              aria-selected={activeLayer === tab.id}
              aria-controls={`panel-${tab.id}`}
            >
              <b>{tab.label}</b><span>{tab.description}</span>
            </button>
          ))}
        </nav>
      </header>

      <div className="page-shell">
        <div className="status-row">
          <span className="status-dot" /> Verified correctness replay
          <span>8 events</span>
          <span>Last displayed refresh: {refreshed}</span>
        </div>

        <section className="layer-panel" id="panel-overview" role="tabpanel" aria-labelledby="tab-overview" hidden={activeLayer !== "overview"}>
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

          <section className="metrics-grid" aria-label="Verified project metrics">
            <MetricCard label="Events in current window" value="8" note="Deterministic test stream" />
            <MetricCard label="View sessions" value="4" note="Three reached cart" />
            <MetricCard label="Unusual products" value="1 of 2" note="Threshold: activity lift ≥ 2.0×" />
            <MetricCard label="PySpark speedup" value="1.207×" note="Eight partitions compared with one" />
          </section>

          <section className="panel">
            <div className="panel-heading"><div><p className="section-label">EXPLORE THE PIPELINE</p><h2>Open an analytical layer</h2></div></div>
            <div className="layer-cards">
              <button onClick={() => setActiveLayer("speed")}><span>01</span><b>Speed Layer</b><small>Kinesis, Lambda and the latest five-minute view</small></button>
              <button onClick={() => setActiveLayer("batch")}><span>02</span><b>Batch Layer</b><small>S3 history and PySpark processing on EMR</small></button>
              <button onClick={() => setActiveLayer("serving")}><span>03</span><b>Serving Layer</b><small>Current activity compared with historical norms</small></button>
            </div>
          </section>
        </section>

        <section className="layer-panel" id="panel-speed" role="tabpanel" aria-labelledby="tab-speed" hidden={activeLayer !== "speed"}>
          <div className="layer-intro">
            <div><p className="section-label">SPEED LAYER</p><h2>Recent clickstream activity</h2><p>Kinesis sends session-partitioned events to Lambda, which updates one-minute counters in DynamoDB.</p></div>
            <div className="route-chip">Kinesis <span>→</span> Lambda <span>→</span> DynamoDB</div>
          </div>
          <section className="panel">
            <div className="panel-heading"><div><p className="section-label">LATEST FIVE-MINUTE WINDOW</p><h2>Current product actions</h2></div><span className="verified-tag">8 events processed</span></div>
            <ProductTable includeBaseline={false} />
            <p className="formula-note">Trend score = views + (3 × carts) + (5 × purchases).</p>
          </section>
          <FunnelPanel />
        </section>

        <section className="layer-panel" id="panel-batch" role="tabpanel" aria-labelledby="tab-batch" hidden={activeLayer !== "batch"}>
          <div className="layer-intro">
            <div><p className="section-label">BATCH LAYER</p><h2>Historical baseline processing</h2><p>Amazon S3 retains the accepted history and EMR PySpark produces recomputable five-minute product averages.</p></div>
            <div className="route-chip">S3 history <span>→</span> EMR PySpark <span>→</span> Baselines</div>
          </div>
          <div className="two-column batch-layout">
            <BenchmarkPanel />
            <section className="panel dataset-panel">
              <div className="panel-heading"><div><p className="section-label">VERIFIED INPUT</p><h2>Dataset preparation</h2></div></div>
              <dl className="dataset-summary">
                <div><dt>Source records</dt><dd>885,129</dd></div>
                <div><dt>Selected rows</dt><dd>200,000</dd></div>
                <div><dt>Valid events</dt><dd>199,965</dd></div>
                <div><dt>Rejected rows</dt><dd>35</dd></div>
                <div><dt>Benchmark events</dt><dd>999,825</dd></div>
                <div><dt>Input size</dt><dd>≈ 290 MB</dd></div>
              </dl>
              <p className="limitation">Rows without a session identifier were rejected because their funnel transitions could not be attributed reliably.</p>
            </section>
          </div>
        </section>

        <section className="layer-panel" id="panel-serving" role="tabpanel" aria-labelledby="tab-serving" hidden={activeLayer !== "serving"}>
          <div className="layer-intro">
            <div><p className="section-label">SERVING LAYER</p><h2>Current activity in historical context</h2><p>The serving view joins recent DynamoDB counters with the five-minute baselines generated by PySpark.</p></div>
            <div className="route-chip">Speed view <span>+</span> Batch view <span>→</span> Decision</div>
          </div>
          <section className="panel">
            <div className="panel-heading">
              <div><p className="section-label">MERGED ANALYTICAL VIEW</p><h2>Product activity compared with history</h2></div>
              <span className="verified-tag">Verified result</span>
            </div>
            <ProductTable />
            <p className="formula-note">A product is labelled unusual when its current score is at least twice its historical five-minute average.</p>
          </section>
          <section className="summary-card serving-answer">
            <div><p className="section-label">ANSWER</p><h2>Product 200 has a 2.0× activity lift</h2><p>Product 100 remains at its normal level. The current funnel shows that the larger loss occurs between cart and purchase.</p></div>
            <aside className="decision-box"><b>Why the merge matters</b><p>Without the historical baseline, a high raw score could simply describe a product that is always popular.</p></aside>
          </section>
          <section className="panel compact-flow">
            <div className="panel-heading"><div><p className="section-label">IMPLEMENTED DATA FLOW</p><h2>How this result is assembled</h2></div></div>
            <div className="merge-flow">
              <div><span>Recent</span><b>DynamoDB buckets</b><small>Views, carts and purchases</small></div>
              <strong>+</strong>
              <div><span>Historical</span><b>S3 baseline</b><small>PySpark five-minute averages</small></div>
              <strong>→</strong>
              <div className="flow-result"><span>Serving answer</span><b>Trend lift + funnel</b><small>Business-readable output</small></div>
            </div>
          </section>
        </section>
      </div>
    </main>
  );
}
