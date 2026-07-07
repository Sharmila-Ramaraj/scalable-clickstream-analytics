import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

test("exports the verified clickstream dashboard for AWS", async () => {
  const html = await readFile(new URL("out/index.html", root), "utf8");

  assert.match(html, /<title>Scalable Real-Time Clickstream Analytics \| X24244066<\/title>/i);
  assert.match(html, /Product 200 is unusually trending/);
  assert.match(html, /activity lift of <strong>2\.0×<\/strong>/);
  assert.match(html, /66\.67%/);
  assert.match(html, /4 sessions/);
  assert.match(html, /3 sessions/);
  assert.match(html, /1 session/);
  assert.match(html, /1\.207×/);
  assert.match(html, /How the result is produced/);
  assert.match(html, /Sharmila Ramaraj/);
  assert.match(html, /X24244066/);
  assert.doesNotMatch(html, /signin-with|signout-with|Your site is taking shape/);
});

test("keeps the student dashboard readable and avoids excessive visual effects", async () => {
  const [page, layout, css, packageJson] = await Promise.all([
    readFile(new URL("app/page.tsx", root), "utf8"),
    readFile(new URL("app/layout.tsx", root), "utf8"),
    readFile(new URL("app/globals.css", root), "utf8"),
    readFile(new URL("package.json", root), "utf8"),
  ]);

  assert.match(page, /useState\("19:39 UTC"\)/);
  assert.match(page, /REAL-TIME ANALYTICAL ANSWER/);
  assert.match(page, /Individual student implementation/);
  assert.match(page, /cart-to-purchase is the larger loss/);
  assert.match(page, /same two-worker cluster/i);
  assert.doesNotMatch(page, /orbit|sceneMode|Pause motion/);
  assert.match(layout, /s3-website-us-east-1\.amazonaws\.com/);
  assert.match(css, /\.funnel-row/);
  assert.match(css, /\.pipeline-step/);
  assert.doesNotMatch(css, /perspective|rotateX|rotateY|rotateZ/);
  assert.match(css, /@media \(max-width:\s*560px\)/);
  assert.match(packageJson, /"build:aws": "next build"/);
});
