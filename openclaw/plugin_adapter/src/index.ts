import { resolveConfig } from "./client/api.js";
import { registerArtifactTools } from "./tools/artifact.js";
import { registerKbTools } from "./tools/kb.js";
import type { OpenClawPlugin } from "./types.js";

const plugin: OpenClawPlugin = {
  name: "agent-foundation-adapter",
  register({ tools, config }) {
    const resolved = resolveConfig(config);
    registerArtifactTools(tools, resolved);
    registerKbTools(tools, resolved);
  }
};

export default plugin;

