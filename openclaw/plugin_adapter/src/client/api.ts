import { randomUUID } from "node:crypto";

import type { PluginConfig, ToolFailure, ToolResult, ToolSuccess } from "../types.js";

export async function requestJson<T>(
  baseUrl: string,
  path: string,
  init: RequestInit,
  timeoutMs: number,
  ctx?: unknown
): Promise<ToolResult<T>> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  const headers = new Headers(init.headers ?? {});
  headers.set("content-type", "application/json");
  if (!headers.has("x-trace-id")) {
    headers.set("x-trace-id", randomUUID());
  }
  const runId = extractRunId(ctx);
  if (runId && !headers.has("x-run-id")) {
    headers.set("x-run-id", runId);
  }
  const traceId = headers.get("x-trace-id") ?? undefined;

  try {
    const response = await fetch(new URL(path, baseUrl), {
      ...init,
      headers,
      signal: controller.signal,
    });
    const responseTraceId = response.headers.get("x-trace-id") ?? traceId;

    const contentType = response.headers.get("content-type") ?? "";
    const data = contentType.includes("application/json")
      ? ((await response.json()) as T)
      : ((await response.text()) as T);

    if (!response.ok) {
      return {
        ok: false,
        error_code: `http_${response.status}`,
        message: extractMessage(data, response.statusText),
        trace_id: responseTraceId,
      };
    }

    return {
      ok: true,
      message: "Request succeeded",
      data,
      trace_id: responseTraceId,
    };
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      return {
        ok: false,
        error_code: "timeout",
        message: `Request timed out after ${timeoutMs}ms`,
        trace_id: traceId,
      };
    }
    return {
      ok: false,
      error_code: "request_failed",
      message: error instanceof Error ? error.message : "Unknown request error",
      trace_id: traceId,
    };
  } finally {
    clearTimeout(timeout);
  }
}

export function resolveConfig(config?: Partial<PluginConfig>): PluginConfig {
  return {
    artifactApiBaseUrl: config?.artifactApiBaseUrl ?? process.env.ARTIFACT_API_BASE_URL ?? "http://127.0.0.1:8081",
    thinKbApiBaseUrl: config?.thinKbApiBaseUrl ?? process.env.THIN_KB_API_BASE_URL ?? "http://127.0.0.1:8082",
    requestTimeoutMs: config?.requestTimeoutMs ?? Number(process.env.REQUEST_TIMEOUT_MS ?? "5000"),
  };
}

function extractMessage(data: unknown, fallback: string): string {
  if (typeof data === "object" && data !== null && "detail" in data && typeof data.detail === "string") {
    return data.detail;
  }
  return fallback || "Request failed";
}

function extractRunId(ctx: unknown): string | undefined {
  if (ctx && typeof ctx === "object") {
    const record = ctx as Record<string, unknown>;
    if (typeof record.run_id === "string" && record.run_id) {
      return record.run_id;
    }
    if (typeof record.runId === "string" && record.runId) {
      return record.runId;
    }
  }
  const envRunId = process.env.OPENCLAW_RUN_ID;
  return envRunId && envRunId.length > 0 ? envRunId : undefined;
}
