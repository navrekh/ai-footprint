import { ApiError, messageForStatus, type ApiErrorBody } from "@/lib/errors/apiError";
import { getApiBaseUrl, getApiKey } from "@/lib/auth/session";

export interface RequestOptions {
  method?: "GET" | "POST" | "PATCH";
  path: string;
  query?: Record<string, string | number | undefined | null>;
  body?: unknown;
  /** Explicit credentials, used by the connection check before a session exists. */
  credentials?: { baseUrl: string; apiKey: string };
  signal?: AbortSignal;
}

function buildUrl(
  baseUrl: string,
  path: string,
  query?: RequestOptions["query"],
): string {
  const url = new URL(`${baseUrl}${path}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null || value === "") continue;
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

async function parseErrorBody(
  response: Response,
): Promise<{ body: ApiErrorBody | null; raw: string | null }> {
  try {
    const text = await response.text();
    if (!text) return { body: null, raw: null };
    try {
      const parsed = JSON.parse(text) as { error?: ApiErrorBody };
      if (parsed && typeof parsed === "object" && parsed.error) {
        return { body: parsed.error, raw: null };
      }
    } catch {
      /* non-JSON error payload */
    }
    return { body: null, raw: text.slice(0, 300) };
  } catch {
    return { body: null, raw: null };
  }
}

/**
 * Single entry point for every console -> AI Footprint API call.
 * Adds the bearer Authorization header, surfaces request IDs, and never
 * logs headers, credentials, or key material.
 */
export async function apiRequest<T>(options: RequestOptions): Promise<T> {
  const baseUrl = options.credentials?.baseUrl ?? getApiBaseUrl();
  const apiKey = options.credentials?.apiKey ?? getApiKey();

  if (!baseUrl) {
    throw new ApiError({
      status: 0,
      code: "CONSOLE_NOT_CONFIGURED",
      message: "No API base URL is configured. Set VITE_API_BASE_URL or enter one when connecting.",
    });
  }
  if (!apiKey) {
    throw new ApiError({
      status: 401,
      code: "UNAUTHORIZED",
      message: messageForStatus(401),
    });
  }

  const headers: Record<string, string> = { Authorization: `Bearer ${apiKey}` };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";

  let response: Response;
  try {
    response = await fetch(buildUrl(baseUrl, options.path, options.query), {
      method: options.method ?? "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal,
      credentials: "omit",
      mode: "cors",
    });
  } catch {
    throw new ApiError({
      status: 0,
      code: "NETWORK_ERROR",
      message:
        "Could not reach the AI Footprint API. Check the API base URL and that the console origin is allowed by the API's CORS configuration.",
    });
  }

  const headerRequestId = response.headers.get("X-Request-ID");

  if (!response.ok) {
    const { body, raw } = await parseErrorBody(response);
    throw new ApiError({
      status: response.status,
      code: body?.code ?? "HTTP_ERROR",
      message: messageForStatus(response.status, body?.message ?? null),
      requestId: body?.request_id ?? headerRequestId,
      detail: body?.message ?? raw,
    });
  }

  if (response.status === 204) return undefined as T;

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError({
      status: response.status,
      code: "INVALID_RESPONSE",
      message: "The API returned a response the console could not read.",
      requestId: headerRequestId,
    });
  }
}
