export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  run: (ctx: unknown, input: Record<string, unknown>) => Promise<unknown>;
}

export interface ToolRegistry {
  register(definition: ToolDefinition): void;
}

export interface PluginConfig {
  artifactApiBaseUrl: string;
  thinKbApiBaseUrl: string;
  requestTimeoutMs: number;
}

export interface OpenClawPlugin {
  name: string;
  register(ctx: { tools: ToolRegistry; config?: Partial<PluginConfig> }): void;
}

export interface ToolSuccess<T = unknown> {
  ok: true;
  message: string;
  data: T;
  trace_id?: string;
}

export interface ToolFailure {
  ok: false;
  error_code: string;
  message: string;
  trace_id?: string;
}

export type ToolResult<T = unknown> = ToolSuccess<T> | ToolFailure;
