/**
 * Test helpers: a fresh QueryClient + in-memory router per render, and a
 * fetch mock that routes by method + path exactly as the backend contract
 * defines. Tests assert on the requests the console actually makes — the
 * mock never fabricates console behavior.
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

export function renderWithProviders(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    );
  }
  return { queryClient, ...render(ui, { wrapper: Wrapper }) };
}

export interface MockRoute {
  method?: string;
  /** Exact path or pattern matched against the request URL path. */
  path: string | RegExp;
  body: unknown;
  status?: number;
}

export interface RecordedCall {
  url: string;
  method: string;
  body: unknown;
  authorization: string | null;
}

export function mockApi(routes: MockRoute[]): RecordedCall[] {
  const calls: RecordedCall[] = [];
  vi.stubGlobal("fetch", async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const method = init?.method ?? "GET";
    const headers = new Headers(init?.headers);
    calls.push({
      url,
      method,
      body: init?.body ? JSON.parse(String(init.body)) : undefined,
      authorization: headers.get("Authorization"),
    });
    const pathname = new URL(url).pathname;
    const route = routes.find((candidate) => {
      const methodMatches = (candidate.method ?? "GET") === method;
      const pathMatches =
        typeof candidate.path === "string"
          ? candidate.path === pathname
          : candidate.path.test(pathname);
      return methodMatches && pathMatches;
    });
    if (!route) {
      return new Response(
        JSON.stringify({
          error: { code: "NOT_FOUND", message: "Not found.", request_id: "req_test" },
        }),
        { status: 404, headers: { "Content-Type": "application/json" } },
      );
    }
    return new Response(JSON.stringify(route.body), {
      status: route.status ?? 200,
      headers: { "Content-Type": "application/json", "X-Request-ID": "req_test" },
    });
  });
  return calls;
}

export const TEST_BASE_URL = "https://api.test";

export function connectSession(rawKey: string) {
  sessionStorage.setItem("aifootprint.console.apiKey", rawKey);
  sessionStorage.setItem("aifootprint.console.apiBaseUrl", TEST_BASE_URL);
}
