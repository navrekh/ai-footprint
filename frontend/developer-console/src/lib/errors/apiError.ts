/**
 * Maps the backend error contract — `{"error": {code, message, request_id}}`
 * plus the `X-Request-ID` response header — to developer-facing messages.
 * Never carries request headers, credentials, or key material.
 */

export interface ApiErrorBody {
  code: string;
  message: string;
  request_id?: string | null;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string | null;
  readonly detail: string | null;

  constructor(params: {
    status: number;
    code: string;
    message: string;
    requestId?: string | null;
    detail?: string | null;
  }) {
    super(params.message);
    this.name = "ApiError";
    this.status = params.status;
    this.code = params.code;
    this.requestId = params.requestId ?? null;
    this.detail = params.detail ?? null;
  }

  get isAuthError(): boolean {
    return this.status === 401;
  }
}

export function messageForStatus(status: number, backendMessage?: string | null): string {
  switch (status) {
    case 400:
      return backendMessage || "The request was invalid.";
    case 401:
      return "Your API key is invalid or expired.";
    case 403:
      return "You don't have permission to access this resource.";
    case 404:
      return "The requested resource could not be found.";
    case 409:
      return backendMessage || "That change conflicts with the current state of the resource.";
    case 422:
      return backendMessage || "Some values were rejected by the API.";
    case 429:
      return "Too many requests. Please try again shortly.";
    default:
      if (status >= 500) return "AI Footprint API encountered an error.";
      return backendMessage || "The request could not be completed.";
  }
}

/** Human-readable summary for any thrown value, safe to render. */
export function describeError(error: unknown): { message: string; requestId: string | null } {
  if (error instanceof ApiError) {
    return { message: error.message, requestId: error.requestId };
  }
  if (error instanceof Error) {
    return { message: error.message, requestId: null };
  }
  return { message: "Something went wrong.", requestId: null };
}
