import { useMemo, useState } from "react";
import { Check, Copy, Loader2, LockKeyhole, Play } from "lucide-react";

import { ErrorState } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { useExecuteRequest, useOpenApiSpec } from "@/hooks/queries";
import {
  listEndpoints,
  pathParameters,
  queryParameters,
  requestBodyExample,
  type ApiEndpoint,
} from "@/lib/api/openapi";
import { describeError } from "@/lib/errors/apiError";

function endpointKey(endpoint: Pick<ApiEndpoint, "method" | "path">): string {
  return `${endpoint.method} ${endpoint.path}`;
}

export function ApiExplorerPage() {
  const spec = useOpenApiSpec();
  const execute = useExecuteRequest();

  const endpoints = useMemo(() => (spec.data ? listEndpoints(spec.data) : []), [spec.data]);
  const [selectedKey, setSelectedKey] = useState<string>("");
  const [pathValues, setPathValues] = useState<Record<string, string>>({});
  const [queryValues, setQueryValues] = useState<Record<string, string>>({});
  const [bodyText, setBodyText] = useState("");
  const [bodyError, setBodyError] = useState<string | null>(null);
  const [copied, setCopied] = useState<"request" | "response" | null>(null);

  const selected = endpoints.find((endpoint) => endpointKey(endpoint) === selectedKey) ?? null;
  const pathParams = selected ? pathParameters(selected.operation) : [];
  const queryParams = selected ? queryParameters(selected.operation) : [];
  const hasBody = Boolean(selected?.operation.requestBody);

  const groups = useMemo(() => {
    const byTag = new Map<string, ApiEndpoint[]>();
    for (const endpoint of endpoints) {
      const list = byTag.get(endpoint.tag) ?? [];
      list.push(endpoint);
      byTag.set(endpoint.tag, list);
    }
    return [...byTag.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [endpoints]);

  function selectEndpoint(key: string) {
    setSelectedKey(key);
    setPathValues({});
    setQueryValues({});
    setBodyError(null);
    execute.reset();
    const endpoint = endpoints.find((candidate) => endpointKey(candidate) === key);
    if (endpoint && spec.data) {
      const example = requestBodyExample(spec.data, endpoint.operation);
      setBodyText(example !== undefined ? JSON.stringify(example, null, 2) : "");
    } else {
      setBodyText("");
    }
  }

  function buildPath(): string | null {
    if (!selected) return null;
    let path = selected.path;
    for (const param of pathParams) {
      const value = pathValues[param.name]?.trim();
      if (!value) return null;
      path = path.replace(`{${param.name}}`, encodeURIComponent(value));
    }
    return path;
  }

  async function handleExecute() {
    if (!selected) return;
    const path = buildPath();
    if (path === null) return;

    let body: unknown;
    setBodyError(null);
    if (hasBody && bodyText.trim()) {
      try {
        body = JSON.parse(bodyText);
      } catch {
        setBodyError("Request body is not valid JSON.");
        return;
      }
    }

    const query: Record<string, string> = {};
    for (const param of queryParams) {
      const value = queryValues[param.name];
      if (value) query[param.name] = value;
    }

    execute.mutate({
      method: selected.method as "GET" | "POST" | "PATCH",
      path,
      query,
      body: hasBody && bodyText.trim() ? body : undefined,
    });
  }

  async function copyText(kind: "request" | "response", text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(kind);
      window.setTimeout(() => setCopied(null), 2000);
    } catch {
      setCopied(null);
    }
  }

  const previewBody = (() => {
    if (!hasBody || !bodyText.trim()) return undefined;
    try {
      return redactCredentialMaterial(JSON.parse(bodyText));
    } catch {
      return "[Request body is not valid JSON]";
    }
  })();
  const requestPreview = selected
    ? JSON.stringify(
        {
          method: selected.method,
          path: buildPath() ?? selected.path,
          query: queryValues,
          headers: { Authorization: "Bearer ••••••••" },
          body: previewBody,
        },
        null,
        2,
      )
    : "";

  const safeResponse = execute.isSuccess ? redactCredentialMaterial(execute.data.data) : undefined;

  return (
    <div className="space-y-6">
      <PageHeader
        title="API Explorer"
        description="Build and execute authenticated requests from the live API contract. Your connected credential remains masked and outside request parameters."
      />

      {spec.isPending ? (
        <p className="text-sm text-muted-foreground">Loading the API contract…</p>
      ) : spec.error ? (
        <ErrorState error={spec.error} onRetry={() => spec.refetch()} />
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-[16rem_minmax(0,1fr)] xl:grid-cols-[16rem_minmax(0,1fr)_minmax(19rem,0.8fr)]">
            <Card className="hidden self-start lg:block">
              <CardHeader><CardTitle>Endpoints</CardTitle></CardHeader>
              <CardContent className="max-h-[70vh] space-y-5 overflow-y-auto p-3">
                {groups.map(([tag, group]) => (
                  <div key={tag}>
                    <p className="px-2 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{tag}</p>
                    <div className="space-y-0.5">
                      {group.map((endpoint) => {
                        const key = endpointKey(endpoint);
                        return (
                          <Button
                            key={key}
                            type="button"
                            variant="ghost"
                            onClick={() => selectEndpoint(key)}
                            className={`grid h-auto w-full grid-cols-[3.25rem_minmax(0,1fr)] justify-start gap-2 px-2 py-2 text-left text-xs ${selectedKey === key ? "bg-muted text-foreground" : ""}`}
                          >
                            <span className="font-mono font-semibold text-primary">{endpoint.method}</span>
                            <span className="truncate font-mono">{endpoint.path.replace("/v1/", "/")}</span>
                          </Button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="min-w-0 self-start">
              <CardHeader className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
                <div className="min-w-0">
                  <CardTitle>Request builder</CardTitle>
                  {selected ? <p className="mt-1 truncate font-mono text-xs text-muted-foreground">{selected.method} {selected.path}</p> : null}
                </div>
                <LockKeyhole className="h-4 w-4 shrink-0 text-success" aria-label="Authenticated securely" />
              </CardHeader>
              <CardContent className="space-y-4">
              <Field label="Endpoint" htmlFor="explorer-endpoint">
                <Select
                  id="explorer-endpoint"
                  value={selectedKey}
                  onChange={(event) => selectEndpoint(event.target.value)}
                >
                  <option value="">Select an endpoint…</option>
                  {groups.map(([tag, group]) => (
                    <optgroup key={tag} label={tag}>
                      {group.map((endpoint) => (
                        <option key={endpointKey(endpoint)} value={endpointKey(endpoint)}>
                          {endpoint.method} {endpoint.path}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </Select>
              </Field>

              {selected ? (
                <>
                  {selected.operation.summary ? (
                    <p className="text-sm text-muted-foreground">{selected.operation.summary}</p>
                  ) : null}

                  {pathParams.length > 0 ? (
                    <div className="grid gap-3 sm:grid-cols-2">
                      {pathParams.map((param) => (
                        <Field
                          key={param.name}
                          label={`${param.name} (path)`}
                          htmlFor={`explorer-path-${param.name}`}
                          hint={param.description}
                        >
                          <Input
                            id={`explorer-path-${param.name}`}
                            value={pathValues[param.name] ?? ""}
                            required
                            onChange={(event) =>
                              setPathValues((prev) => ({ ...prev, [param.name]: event.target.value }))
                            }
                          />
                        </Field>
                      ))}
                    </div>
                  ) : null}

                  {queryParams.length > 0 ? (
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                      {queryParams.map((param) => (
                        <Field
                          key={param.name}
                          label={`${param.name} (query)`}
                          htmlFor={`explorer-query-${param.name}`}
                          hint={param.description}
                        >
                          <Input
                            id={`explorer-query-${param.name}`}
                            value={queryValues[param.name] ?? ""}
                            onChange={(event) =>
                              setQueryValues((prev) => ({ ...prev, [param.name]: event.target.value }))
                            }
                          />
                        </Field>
                      ))}
                    </div>
                  ) : null}

                  {hasBody ? (
                    <Field
                      label="Request body (JSON)"
                      htmlFor="explorer-body"
                      error={bodyError}
                    >
                      <Textarea
                        id="explorer-body"
                        className="min-h-40 font-mono text-xs"
                        value={bodyText}
                        onChange={(event) => setBodyText(event.target.value)}
                      />
                    </Field>
                  ) : null}

                  <p className="font-mono text-xs text-muted-foreground">
                    Authorization: Bearer ••••••••
                  </p>

                  <div className="flex flex-wrap items-center gap-2 border-t border-border pt-4">
                    <Button onClick={handleExecute} disabled={execute.isPending}>
                      {execute.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                      ) : null}
                      <Play className="h-3.5 w-3.5" aria-hidden="true" />
                      Execute request
                    </Button>
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={() => copyText("request", requestPreview)}
                    >
                      {copied === "request" ? (
                        <Check className="h-4 w-4" aria-hidden="true" />
                      ) : (
                        <Copy className="h-4 w-4" aria-hidden="true" />
                      )}
                      Copy request
                    </Button>
                  </div>
                </>
              ) : null}
              </CardContent>
            </Card>

          <div className="min-w-0 xl:sticky xl:top-6 xl:self-start">
          {execute.isSuccess || execute.isError ? (
            <Card className="min-w-0">
              <CardHeader className="flex flex-row items-center justify-between gap-3">
                <CardTitle>Response</CardTitle>
                {execute.isSuccess ? (
                  <Badge tone="active">{execute.data.status}</Badge>
                ) : (
                  <Badge tone="danger">Error</Badge>
                )}
              </CardHeader>
              <CardContent className="space-y-3">
                {execute.isSuccess ? (
                  <>
                    <p className="font-mono text-xs text-muted-foreground">
                      Request ID: {execute.data.requestId ?? "—"}
                    </p>
                     <ResponseBody value={safeResponse} onCopy={(text) => copyText("response", text)} copied={copied === "response"} />
                  </>
                ) : (
                  <ExecuteErrorView error={execute.error} />
                )}
              </CardContent>
            </Card>
          ) : (
            <Card className="border-dashed">
              <CardContent className="py-14 text-center">
                <p className="text-sm font-medium">Response workspace</p>
                <p className="mt-1 text-xs text-muted-foreground">Select an endpoint, provide its parameters, and execute the request.</p>
              </CardContent>
            </Card>
          )}
          </div>
          </div>
        </>
      )}
    </div>
  );
}

function ResponseBody({
  value,
  onCopy,
  copied,
}: {
  value: unknown;
  onCopy: (text: string) => void;
  copied: boolean;
}) {
  const text = JSON.stringify(value, null, 2);
  return (
    <div className="space-y-2">
      <pre className="max-h-96 overflow-auto rounded-[var(--radius-console)] border border-border bg-input px-3 py-3 font-mono text-xs">
        {text}
      </pre>
      <Button type="button" variant="secondary" size="sm" onClick={() => onCopy(text)}>
        {copied ? <Check className="h-4 w-4" aria-hidden="true" /> : <Copy className="h-4 w-4" aria-hidden="true" />}
        Copy response
      </Button>
    </div>
  );
}

function ExecuteErrorView({ error }: { error: unknown }) {
  const { message, requestId } = describeError(error);
  return (
    <div className="space-y-1">
      <p className="text-sm text-foreground">{message}</p>
      {requestId ? (
        <p className="font-mono text-xs text-muted-foreground">Request ID: {requestId}</p>
      ) : null}
    </div>
  );
}

function redactCredentialMaterial(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(redactCredentialMaterial);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [
      key,
      /^(key|api_key|access_token|authorization)$/i.test(key)
        ? "[REDACTED]"
        : redactCredentialMaterial(item),
    ]),
  );
}
