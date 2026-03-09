import test from "node:test";
import assert from "node:assert/strict";

const calls = [];

globalThis.fetch = async (url, init) => {
  calls.push({ url: String(url), init });
  return new Response(
    JSON.stringify({
      ok: "service-response",
      path: String(url)
    }),
    {
      status: 200,
      headers: { "content-type": "application/json" }
    }
  );
};

test("plugin registers artifact and kb tools and forwards calls", async () => {
  calls.length = 0;
  const registry = new Map();
  const { default: plugin } = await import("../dist/index.js");

  plugin.register({
    tools: {
      register(definition) {
        registry.set(definition.name, definition);
      }
    },
    config: {
      artifactApiBaseUrl: "http://artifact.local",
      thinKbApiBaseUrl: "http://kb.local",
      requestTimeoutMs: 100
    }
  });

  assert.ok(registry.has("artifact_get"));
  assert.ok(registry.has("artifact_create_task"));
  assert.ok(registry.has("kb_search"));
  assert.ok(registry.has("kb_ingest_document"));
  assert.ok(registry.has("kb_search_hybrid"));
  assert.ok(registry.has("kb_refine_writeback"));

  const artifactResult = await registry.get("artifact_get").run({}, {
    task_id: "task-1",
    stage: "00_task",
    name: "task-brief.json"
  });
  assert.equal(artifactResult.ok, true);
  assert.match(calls.at(-1).url, /http:\/\/artifact\.local\/v1\/tasks\/task-1\/artifacts\/00_task\/task-brief\.json/);

  const kbResult = await registry.get("kb_search").run({}, {
    query: "fts",
    object_type: "claim",
    version: "1.0.0"
  });
  assert.equal(kbResult.ok, true);
  assert.match(calls.at(-1).url, /http:\/\/kb\.local\/v1\/kb\/claims\/search/);
  assert.match(String(calls.at(-1).init.body), /"version":"1.0.0"/);
  assert.ok(new Headers(calls.at(-1).init.headers).get("x-trace-id"));
  assert.ok(kbResult.trace_id);

  const hybridResult = await registry.get("kb_search_hybrid").run({ run_id: "run-shadow-1" }, {
    query: "hybrid retrieval",
    source_types: ["document"]
  });
  assert.equal(hybridResult.ok, true);
  assert.match(calls.at(-1).url, /http:\/\/kb\.local\/v1\/kb\/search\/hybrid/);
  assert.equal(new Headers(calls.at(-1).init.headers).get("x-run-id"), "run-shadow-1");

  const refineResult = await registry.get("kb_refine_writeback").run({}, {
    task_id: "task-1",
    persist: true
  });
  assert.equal(refineResult.ok, true);
  assert.match(calls.at(-1).url, /http:\/\/kb\.local\/v1\/kb\/writeback\/refine/);
});

test("plugin preserves API boundary failures as normalized errors", async () => {
  calls.length = 0;
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return new Response(
      JSON.stringify({
        detail: "ExperiencePacket cannot be finalized before VALIDATED"
      }),
      {
        status: 409,
        headers: {
          "content-type": "application/json",
          "x-trace-id": "trace-failure-1"
        }
      }
    );
  };

  try {
    const registry = new Map();
    const { default: plugin } = await import("../dist/index.js");

    plugin.register({
      tools: {
        register(definition) {
          registry.set(definition.name, definition);
        }
      },
      config: {
        artifactApiBaseUrl: "http://artifact.local",
        thinKbApiBaseUrl: "http://kb.local",
        requestTimeoutMs: 100
      }
    });

    const result = await registry.get("artifact_finalize_experience").run({}, { task_id: "task-early" });
    assert.equal(result.ok, false);
    assert.equal(result.error_code, "http_409");
    assert.equal(result.message, "ExperiencePacket cannot be finalized before VALIDATED");
    assert.equal(result.trace_id, "trace-failure-1");
  } finally {
    globalThis.fetch = originalFetch;
  }
});
