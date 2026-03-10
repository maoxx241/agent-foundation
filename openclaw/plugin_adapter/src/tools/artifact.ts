import { requestJson } from "../client/api.js";
import type { PluginConfig, ToolRegistry } from "../types.js";

export function registerArtifactTools(tools: ToolRegistry, config: PluginConfig): void {
  tools.register({
    name: "artifact_create_task",
    description: "Create a task workspace in the artifact service.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["task_id", "project_id", "title", "goal"],
      properties: {
        task_id: { type: "string" },
        project_id: { type: "string" },
        title: { type: "string" },
        goal: { type: "string" },
        description: { type: "string" },
        requester: { type: "string" },
        priority: { type: "string" },
        domain_tags: { type: "array", items: { type: "string" } },
        env: { type: "object" },
        acceptance_hint: { type: "string" },
        initial_refs: { type: "array", items: { type: "object" } }
      }
    },
    async run(ctx, input) {
      return requestJson(config.artifactApiBaseUrl, "/v1/tasks", {
        method: "POST",
        body: JSON.stringify(input),
      }, config.requestTimeoutMs, ctx, config.serviceToken);
    }
  });

  tools.register({
    name: "artifact_get",
    description: "Fetch one artifact from the artifact service.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["task_id", "stage", "name"],
      properties: {
        task_id: { type: "string" },
        stage: { type: "string" },
        name: { type: "string" }
      }
    },
    async run(ctx, input) {
      return requestJson(
        config.artifactApiBaseUrl,
        `/v1/tasks/${input.task_id}/artifacts/${input.stage}/${input.name}`,
        { method: "GET" },
        config.requestTimeoutMs,
        ctx,
        config.serviceToken
      );
    }
  });

  tools.register({
    name: "artifact_put",
    description: "Write one artifact into the artifact service.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["task_id", "stage", "name", "format", "content"],
      properties: {
        task_id: { type: "string" },
        stage: { type: "string" },
        name: { type: "string" },
        format: { type: "string", enum: ["json", "markdown", "text"] },
        content: {}
      }
    },
    async run(ctx, input) {
      const { task_id, stage, name, ...body } = input;
      return requestJson(
        config.artifactApiBaseUrl,
        `/v1/tasks/${task_id}/artifacts/${stage}/${name}`,
        {
          method: "PUT",
          body: JSON.stringify(body),
        },
        config.requestTimeoutMs,
        ctx,
        config.serviceToken
      );
    }
  });

  tools.register({
    name: "artifact_list",
    description: "List artifacts for one task.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["task_id"],
      properties: {
        task_id: { type: "string" }
      }
    },
    async run(ctx, input) {
      return requestJson(
        config.artifactApiBaseUrl,
        `/v1/tasks/${input.task_id}/artifacts`,
        { method: "GET" },
        config.requestTimeoutMs,
        ctx,
        config.serviceToken
      );
    }
  });

  tools.register({
    name: "artifact_update_state",
    description: "Validate and update a task state.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["task_id", "target_state", "changed_by"],
      properties: {
        task_id: { type: "string" },
        target_state: { type: "string" },
        changed_by: { type: "string" },
        reason: { type: "string" }
      }
    },
    async run(ctx, input) {
      const { task_id, ...body } = input;
      return requestJson(
        config.artifactApiBaseUrl,
        `/v1/tasks/${task_id}/state`,
        {
          method: "PATCH",
          body: JSON.stringify(body),
        },
        config.requestTimeoutMs,
        ctx,
        config.serviceToken
      );
    }
  });

  tools.register({
    name: "artifact_finalize_experience",
    description: "Finalize the experience packet for writeback.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["task_id"],
      properties: {
        task_id: { type: "string" }
      }
    },
    async run(ctx, input) {
      return requestJson(
        config.artifactApiBaseUrl,
        `/v1/tasks/${input.task_id}/experience/finalize`,
        { method: "POST" },
        config.requestTimeoutMs,
        ctx,
        config.serviceToken
      );
    }
  });
}
