/**
 * Minimal OpenAPI 3.1 types/helpers for the API Explorer — enough to list
 * endpoints and pre-fill an example request body, without embedding a
 * third-party Swagger UI (which persists its own auth state in
 * localStorage by default, violating ADR-012's sessionStorage-only rule).
 * Endpoints are read from the backend's own generated `/openapi.json`
 * rather than hand-maintained here, so there is exactly one contract.
 */
import { apiRequest } from "@/lib/api/client";

export interface OpenApiParameter {
  name: string;
  in: "query" | "path" | "header" | "cookie";
  required?: boolean;
  description?: string;
  schema?: { type?: string; description?: string; default?: unknown };
}

export interface OpenApiOperation {
  summary?: string;
  description?: string;
  tags?: string[];
  parameters?: OpenApiParameter[];
  requestBody?: {
    content?: Record<string, { schema?: Record<string, unknown> }>;
  };
}

export interface OpenApiDocument {
  paths: Record<string, Record<string, OpenApiOperation>>;
  components?: { schemas?: Record<string, Record<string, unknown>> };
}

const HTTP_METHODS = ["get", "post", "put", "patch", "delete"] as const;

export interface ApiEndpoint {
  method: string;
  path: string;
  tag: string;
  operation: OpenApiOperation;
}

export function listEndpoints(spec: OpenApiDocument): ApiEndpoint[] {
  const endpoints: ApiEndpoint[] = [];
  for (const [path, methods] of Object.entries(spec.paths ?? {})) {
    for (const method of HTTP_METHODS) {
      const operation = methods[method];
      if (operation) {
        endpoints.push({
          method: method.toUpperCase(),
          path,
          tag: operation.tags?.[0] ?? "other",
          operation,
        });
      }
    }
  }
  return endpoints.sort((a, b) =>
    a.tag === b.tag
      ? a.path === b.path
        ? a.method.localeCompare(b.method)
        : a.path.localeCompare(b.path)
      : a.tag.localeCompare(b.tag),
  );
}

function resolveSchema(
  spec: OpenApiDocument,
  schema: Record<string, unknown> | undefined,
): Record<string, unknown> | undefined {
  if (!schema) return undefined;
  const ref = schema.$ref as string | undefined;
  if (ref?.startsWith("#/components/schemas/")) {
    const name = ref.replace("#/components/schemas/", "");
    return spec.components?.schemas?.[name] ?? schema;
  }
  return schema;
}

/** The Pydantic `json_schema_extra` example for an operation's request
 * body, if the backend defined one — used only to pre-fill the JSON
 * textarea; never invented when absent. */
export function requestBodyExample(spec: OpenApiDocument, operation: OpenApiOperation): unknown {
  const schema = operation.requestBody?.content?.["application/json"]?.schema;
  const resolved = resolveSchema(spec, schema);
  return resolved?.example;
}

export function pathParameters(operation: OpenApiOperation): OpenApiParameter[] {
  return (operation.parameters ?? []).filter((p) => p.in === "path");
}

export function queryParameters(operation: OpenApiOperation): OpenApiParameter[] {
  return (operation.parameters ?? []).filter((p) => p.in === "query");
}

export const openApiApi = {
  /** `/openapi.json` is served at the API root, not under `/v1`, and
   * requires no authentication — but the console is already connected by
   * the time this page is reachable, so reusing the same authenticated
   * client is simpler than a one-off unauthenticated fetch. */
  get: () => apiRequest<OpenApiDocument>({ path: "/openapi.json" }),
};
