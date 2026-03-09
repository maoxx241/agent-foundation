import type { OpenClawPlugin } from "openclaw";

const plugin: OpenClawPlugin = {
  name: "agent-foundation-adapter",
  register({ tools }) {
    tools.register({
      name: "artifact_get",
      description: "Fetch one artifact from the artifact service.",
      inputSchema: {
        type: "object",
        additionalProperties: false,
        properties: {
          task_id: { type: "string" },
          stage: { type: "string" },
          name: { type: "string" }
        },
        required: ["task_id", "stage", "name"]
      },
      async run(_ctx, input) {
        // TODO: forward to artifact API
        return { ok: false, message: "Not implemented yet", input };
      }
    });
  }
};

export default plugin;
