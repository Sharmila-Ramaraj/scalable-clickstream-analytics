import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the verified clickstream dashboard", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>StreamCart \| Real-Time Clickstream Analytics<\/title>/i);
  assert.match(html, /Product 200 is unusually trending/);
  assert.match(html, /2\.0x its historical baseline/);
  assert.match(html, /66\.67% drop-off/);
  assert.match(html, /1\.207x/);
  assert.match(html, /AWS data flow/);
  assert.match(html, /Sharmila Ramaraj/);
  assert.match(html, /X24244066/);
  assert.doesNotMatch(html, /Your site is taking shape|Building your site/);
});

test("keeps the 3D demonstration interactive, responsive, and accessible", async () => {
  const [page, layout, css, packageJson] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  assert.match(page, /useState<"trend" \| "pipeline">\("trend"\)/);
  assert.match(page, /aria-label="3D scene controls"/);
  assert.match(page, /aria-pressed=\{running\}/);
  assert.match(page, /Pause motion/);
  assert.match(page, /Verified result/);
  assert.match(page, /Same two-worker cluster/);
  assert.match(layout, /generateMetadata/);
  assert.match(layout, /og\.png/);
  assert.match(css, /prefers-reduced-motion:\s*reduce/);
  assert.match(css, /@media \(max-width:\s*720px\)/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
});
