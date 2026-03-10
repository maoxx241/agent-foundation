import { requestJson } from "../client/api.js";
import type { PluginConfig, ToolRegistry } from "../types.js";

export function registerKbTools(tools: ToolRegistry, config: PluginConfig): void {
  tools.register({
    name: "kb_search",
    description: "Search canonical Thin KB objects.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        query: { type: "string" },
        object_type: { type: "string", enum: ["claim", "procedure", "case", "decision"] },
        object_types: {
          type: "array",
          items: { type: "string", enum: ["claim", "procedure", "case", "decision"] }
        },
        domain_tags: { type: "array", items: { type: "string" } },
        version: { type: "string" },
        status: { type: "string" },
        scope: { type: "string" },
        limit: { type: "integer", minimum: 1, maximum: 100 },
        env_filters: { type: "object" }
      }
    },
    async run(ctx, input) {
      const objectType = typeof input.object_type === "string" ? input.object_type : undefined;
      const specificRoute = objectType ? `/v1/kb/${objectType}s/search` : "/v1/kb/search";
      const body = objectType
        ? {
            query: input.query ?? "",
            domain_tags: input.domain_tags ?? [],
            version: input.version,
            status: input.status,
            scope: input.scope,
            limit: input.limit ?? 10,
            env_filters: input.env_filters ?? {}
          }
        : {
            query: input.query ?? "",
            object_types: input.object_types ?? [],
            domain_tags: input.domain_tags ?? [],
            version: input.version,
            status: input.status,
            scope: input.scope,
            limit: input.limit ?? 10,
            env_filters: input.env_filters ?? {}
          };

      return requestJson(config.thinKbApiBaseUrl, specificRoute, {
        method: "POST",
        body: JSON.stringify(body),
      }, config.requestTimeoutMs, ctx, config.serviceToken);
    }
  });

  tools.register({
    name: "kb_get",
    description: "Fetch one Thin KB object.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["id"],
      properties: {
        id: { type: "string" }
      }
    },
    async run(ctx, input) {
      return requestJson(
        config.thinKbApiBaseUrl,
        `/v1/kb/object/${input.id}`,
        { method: "GET" },
        config.requestTimeoutMs,
        ctx,
        config.serviceToken
      );
    }
  });

  tools.register({
    name: "kb_related",
    description: "Fetch directly related Thin KB objects.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["id"],
      properties: {
        id: { type: "string" }
      }
    },
    async run(ctx, input) {
      return requestJson(
        config.thinKbApiBaseUrl,
        `/v1/kb/related/${input.id}`,
        { method: "GET" },
        config.requestTimeoutMs,
        ctx,
        config.serviceToken
      );
    }
  });

  tools.register({
    name: "kb_ingest_document",
    description: "Ingest a document into the Phase 2 Thin KB extraction layer.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        title: { type: "string" },
        path: { type: "string" },
        content: { type: "string" },
        content_type: { type: "string" },
        language: { type: "string" },
        domain_tags: { type: "array", items: { type: "string" } },
        metadata: { type: "object" }
      }
    },
    async run(ctx, input) {
      return requestJson(config.thinKbApiBaseUrl, "/v1/kb/ingest/document", {
        method: "POST",
        body: JSON.stringify({
          title: input.title,
          path: input.path,
          content: input.content,
          content_type: input.content_type,
          language: input.language,
          domain_tags: input.domain_tags ?? [],
          metadata: input.metadata ?? {}
        }),
      }, config.requestTimeoutMs, ctx, config.serviceToken);
    }
  });

  tools.register({
    name: "kb_ingest_code",
    description: "Ingest code into the Phase 2 Thin KB extraction layer.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        title: { type: "string" },
        path: { type: "string" },
        content: { type: "string" },
        language: { type: "string" },
        domain_tags: { type: "array", items: { type: "string" } },
        metadata: { type: "object" }
      }
    },
    async run(ctx, input) {
      return requestJson(config.thinKbApiBaseUrl, "/v1/kb/ingest/code", {
        method: "POST",
        body: JSON.stringify({
          title: input.title,
          path: input.path,
          content: input.content,
          language: input.language,
          domain_tags: input.domain_tags ?? [],
          metadata: input.metadata ?? {}
        }),
      }, config.requestTimeoutMs, ctx, config.serviceToken);
    }
  });

  tools.register({
    name: "kb_search_hybrid",
    description: "Run hybrid retrieval across canonical KB objects and extracted chunks.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["query"],
      properties: {
        query: { type: "string" },
        object_types: {
          type: "array",
          items: { type: "string", enum: ["claim", "procedure", "case", "decision"] }
        },
        source_types: {
          type: "array",
          items: { type: "string", enum: ["document", "code"] }
        },
        domain_tags: { type: "array", items: { type: "string" } },
        version: { type: "string" },
        status: { type: "string" },
        scope: { type: "string" },
        limit: { type: "integer", minimum: 1, maximum: 100 },
        env_filters: { type: "object" }
      }
    },
    async run(ctx, input) {
      return requestJson(config.thinKbApiBaseUrl, "/v1/kb/search/hybrid", {
        method: "POST",
        body: JSON.stringify({
          query: input.query,
          object_types: input.object_types ?? [],
          source_types: input.source_types ?? [],
          domain_tags: input.domain_tags ?? [],
          version: input.version,
          status: input.status,
          scope: input.scope,
          limit: input.limit ?? 10,
          env_filters: input.env_filters ?? {}
        }),
      }, config.requestTimeoutMs, ctx, config.serviceToken);
    }
  });

  tools.register({
    name: "kb_refine_writeback",
    description: "Refine an ExperiencePacket into candidate canonical KB objects.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        task_id: { type: "string" },
        experience_packet: { type: "object" },
        persist: { type: "boolean" }
      }
    },
    async run(ctx, input) {
      return requestJson(config.thinKbApiBaseUrl, "/v1/kb/writeback/refine", {
        method: "POST",
        body: JSON.stringify({
          task_id: input.task_id,
          experience_packet: input.experience_packet,
          persist: input.persist ?? false
        }),
      }, config.requestTimeoutMs, ctx, config.serviceToken);
    }
  });
}
