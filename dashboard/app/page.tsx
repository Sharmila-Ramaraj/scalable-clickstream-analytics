"use client";

import { useMemo, useState } from "react";

const products = [
  { id: "200", signal: "Unusual surge", views: 2, carts: 1, purchases: 0, score: 5, baseline: 2.5, lift: 2, trending: true },
  { id: "100", signal: "Normal activity", views: 2, carts: 2, purchases: 1, score: 13, baseline: 13, lift: 1, trending: false },
];

const services = [
  { code: "KS", name: "Kinesis", detail: "Event stream ready", tone: "teal" },
  { code: "L", name: "Lambda", detail: "Consumer healthy", tone: "blue" },
  { code: "DB", name: "DynamoDB", detail: "3 live aggregate rows", tone: "violet" },
  { code: "S3", name: "Amazon S3", detail: "History + baselines", tone: "amber" },
  { code: "EMR", name: "EMR Spark", detail: "Benchmark complete", tone: "rose" },
];

function MetricCard({ label, value, note, accent, index }: { label: string; value: string; note: string; accent: string; index: string }) {
  return (
    <article className={`metric-card ${accent}`}>
      <span className="metric-index">{index}</span>
      <p>{label}</p>
      <strong>{value}</strong>
      <span className="metric-note">{note}</span>
      <i className="metric-glow" />
    </article>
  );
}

export default function Home() {
  const [windowSize, setWindowSize] = useState("5m");
  const [refreshed, setRefreshed] = useState("19:39 UTC");
  const [sceneMode, setSceneMode] = useState<"trend" | "pipeline">("trend");
  const [running, setRunning] = useState(true);
  const answer = useMemo(
    () => (windowSize === "5m" ? "Product 200 is unusually trending" : "Five-minute evidence is the verified view"),
    [windowSize],
  );

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark"><i />SC</span>
          <span><b>StreamCart</b><small>3D clickstream intelligence</small></span>
        </div>
        <nav aria-label="Dashboard sections">
          <a className="nav-item active" href="#overview"><span>01</span>Overview</a>
          <a className="nav-item" href="#products"><span>02</span>Product trends</a>
          <a className="nav-item" href="#funnel"><span>03</span>Funnel</a>
          <a className="nav-item" href="#performance"><span>04</span>Performance</a>
          <a className="nav-item" href="#system"><span>05</span>AWS system</a>
        </nav>
        <div className="sidebar-orbit" aria-hidden="true"><i /><i /><i /><span>LIVE</span></div>
        <div className="sidebar-card"><span className="pulse" /><div><b>Pipeline verified</b><small>us-east-1</small></div></div>
        <div className="identity"><span>SR</span><div><b>Sharmila Ramaraj</b><small>X24244066</small></div></div>
      </aside>

      <section className="workspace" id="overview">
        <header className="topbar">
          <div><p className="eyebrow">REAL-TIME E-COMMERCE ANALYTICS</p><h1>Clickstream command centre</h1></div>
          <div className="topbar-actions">
            <span className="mode-badge"><i /> 3D DEMO MODE</span>
            <div className="window-switch" aria-label="Analytics window">
              {[["1m", "1 minute"], ["5m", "5 minutes"], ["15m", "15 minutes"]].map(([short, full]) => (
                <button key={short} title={short === "5m" ? "Verified analytics window" : `${full} preview`} className={windowSize === short ? "selected" : ""} onClick={() => setWindowSize(short)}>{short}</button>
              ))}
            </div>
            <button className="refresh" onClick={() => setRefreshed("just now")}>Refresh</button>
          </div>
        </header>

        <div className="context-strip">
          <span><i className="dot" /> Live correctness fixture</span><span>Last refresh: {refreshed}</span><span>Window: {windowSize === "5m" ? "verified 5 minutes" : windowSize}</span>
        </div>

        <section className="hero-3d">
          <div className="hero-copy">
            <p className="eyebrow light">CURRENT DECISION SIGNAL</p>
            <h2>{answer}</h2>
            <p>Activity is <strong>2.0x its historical baseline</strong>. The larger funnel loss is after cart, so investigate purchase friction before increasing promotion.</p>
            <div className="decision-tags"><span>Product 200</span><span>Lift 2.0x</span><span>High priority</span></div>
            <div className="scene-controls" aria-label="3D scene controls">
              <button className={sceneMode === "trend" ? "active" : ""} aria-pressed={sceneMode === "trend"} onClick={() => setSceneMode("trend")}>Trend signal</button>
              <button className={sceneMode === "pipeline" ? "active" : ""} aria-pressed={sceneMode === "pipeline"} onClick={() => setSceneMode("pipeline")}>AWS data flow</button>
              <button className="play-control" aria-pressed={running} onClick={() => setRunning((value) => !value)}>{running ? "Pause motion" : "Play motion"}</button>
            </div>
          </div>

          <div className={`data-stage mode-${sceneMode} ${running ? "is-running" : "is-paused"}`} aria-label={sceneMode === "trend" ? "3D trend signal for product 200" : "Animated AWS processing path"}>
            <div className="stage-grid" />
            <div className="stage-hud"><span><i /> LIVE</span><b>8 EVENTS</b></div>
            <div className="orbit-rig" aria-hidden="true">
              <i className="orbit orbit-one" /><i className="orbit orbit-two" /><i className="orbit orbit-three" />
              <span className="event-node node-view"><b>2</b><small>VIEWS</small></span>
              <span className="event-node node-cart"><b>1</b><small>CART</small></span>
              <span className="event-node node-buy"><b>0</b><small>BUY</small></span>
              <div className="signal-core"><span>PRODUCT</span><b>#200</b><small>2.0x LIFT</small></div>
            </div>
            <div className="pipeline-rail" aria-hidden="true">
              <span className="rail-node producer">Producer</span><i className="rail-line one" /><span className="rail-node kinesis">Kinesis</span><i className="rail-line two" /><span className="rail-node lambda">Lambda</span><i className="rail-line three" /><span className="rail-node dynamo">DynamoDB</span>
              <b className="data-particle p1" /><b className="data-particle p2" /><b className="data-particle p3" />
            </div>
            <div className="baseline-deck"><span>HISTORICAL BASELINE</span><b>2.5</b><small>CURRENT SCORE 5</small></div>
            <p className="stage-caption">{sceneMode === "trend" ? "Recent activity rises above the historical plane" : "Events travel from replay producer to the speed view"}</p>
          </div>
        </section>

        <section className="demo-path" aria-label="Suggested demonstration sequence">
          <div><span>01</span><p><b>Detect</b>Product 200 reaches 2.0x lift</p></div><i>→</i>
          <div><span>02</span><p><b>Compare</b>Current score against history</p></div><i>→</i>
          <div><span>03</span><p><b>Locate</b>66.67% loss after cart</p></div><i>→</i>
          <div><span>04</span><p><b>Measure</b>Parallel batch is 17.1% faster</p></div>
        </section>

        <section className="metrics-grid" aria-label="Key metrics">
          <MetricCard index="A" label="Events in live window" value="8" note="Deterministic correctness replay" accent="cyan" />
          <MetricCard index="B" label="Active view sessions" value="4" note="3 reached cart" accent="indigo" />
          <MetricCard index="C" label="Unusual products" value="1" note="Out of 2 evaluated products" accent="orange" />
          <MetricCard index="D" label="PySpark speedup" value="1.207x" note="8 partitions vs. 1" accent="green" />
        </section>

        <div className="content-grid">
          <section className="panel depth-panel products-panel" id="products">
            <div className="panel-heading"><div><p className="eyebrow">LIVE + HISTORICAL VIEW</p><h2>Product activity</h2></div><span className="verified-pill">Verified result</span></div>
            <div className="table-wrap"><table>
              <thead><tr><th>Product</th><th>Signal</th><th>Current</th><th>Baseline</th><th>Lift</th></tr></thead>
              <tbody>{products.map((product) => (
                <tr key={product.id}>
                  <td><span className="product-cube"><i>P</i></span><b>#{product.id}</b></td>
                  <td><span className={`signal ${product.trending ? "hot" : "normal"}`}>{product.signal}</span></td>
                  <td><b>{product.score}</b><small>{product.views}V · {product.carts}C · {product.purchases}P</small></td>
                  <td>{product.baseline.toFixed(1)}</td><td><span className={`lift ${product.trending ? "hot" : ""}`}>{product.lift.toFixed(1)}x</span></td>
                </tr>
              ))}</tbody>
            </table></div>
            <p className="panel-note">Trend score = views + 3 × carts + 5 × purchases. Unusual trend threshold = 2.0x historical average.</p>
          </section>

          <section className="panel depth-panel funnel-panel" id="funnel">
            <div className="panel-heading"><div><p className="eyebrow">3D SESSION FUNNEL</p><h2>Where users drop off</h2></div></div>
            <div className="funnel-3d">
              <div className="funnel-slab views"><span><b>4</b>Viewed</span><small>100%</small></div><div className="drop-marker"><i />25% drop-off</div>
              <div className="funnel-slab carts"><span><b>3</b>Added to cart</span><small>75%</small></div><div className="drop-marker danger"><i />66.67% drop-off</div>
              <div className="funnel-slab purchases"><span><b>1</b>Purchased</span><small>25%</small></div>
            </div>
            <div className="insight"><span>!</span><p><b>Primary friction point</b>Cart-to-purchase loss is 2.67x higher than view-to-cart loss.</p></div>
          </section>

          <section className="panel depth-panel performance-panel" id="performance">
            <div className="panel-heading"><div><p className="eyebrow">PYSPARK ON AMAZON EMR</p><h2>3D batch performance</h2></div><span className="dataset-pill">999,825 events · ~290 MB</span></div>
            <div className="performance-layout">
              <div className="bar-chart" aria-label="Batch duration comparison">
                <div className="axis-labels"><span>80s</span><span>60s</span><span>40s</span><span>20s</span><span>0s</span></div>
                <div className="bar-area"><div className="grid-lines"><i/><i/><i/><i/><i/></div>
                  <div className="bar-column"><span className="bar-value">70s</span><div className="bar bar-3d sequential"/><b>1 partition</b><small>Reference</small></div>
                  <div className="bar-column"><span className="bar-value">58s</span><div className="bar bar-3d parallel"/><b>8 partitions</b><small>Parallel</small></div>
                </div>
              </div>
              <div className="performance-summary"><div><small>Time saved</small><b>12 sec</b></div><div><small>Duration reduction</small><b>17.1%</b></div><div><small>Relative speedup</small><b>1.207x</b></div><p>Same two-worker cluster. This measures partition parallelism, not worker-count scaling.</p></div>
            </div>
          </section>

          <section className="panel depth-panel system-panel" id="system">
            <div className="panel-heading"><div><p className="eyebrow">AWS LAMBDA ARCHITECTURE</p><h2>System constellation</h2></div><span className="region">us-east-1</span></div>
            <div className="service-list">{services.map((service) => (
              <div className="service" key={service.name}><span className={`service-cube ${service.tone}`}><i>{service.code}</i></span><div><b>{service.name}</b><small>{service.detail}</small></div><i className="healthy" title="Verified" /></div>
            ))}</div>
            <div className="architecture-line"><span>Producer</span><i>→</i><span>Kinesis</span><i>→</i><span>Lambda</span><i>→</i><span>DynamoDB</span></div>
          </section>
        </div>

        <footer><p><b>Scalable Real-Time E-Commerce Clickstream Analytics</b> · Sharmila Ramaraj · X24244066</p><p>Source: anonymised REES46 electronics events · AWS Academy Learner Lab</p></footer>
      </section>
    </main>
  );
}
