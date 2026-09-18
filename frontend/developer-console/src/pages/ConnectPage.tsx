import { useState, type FormEvent } from "react";
import { Eye, EyeOff, Loader2 } from "lucide-react";

import { InlineError } from "@/components/ErrorState";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { verifyCredentials } from "@/lib/api/resources";
import { DEFAULT_API_BASE_URL, normalizeBaseUrl, setSession } from "@/lib/auth/session";

/**
 * Connection screen (ADR-012). The key is verified against a real
 * authenticated endpoint before the session is stored; authentication is
 * never assumed to succeed.
 */
export function ConnectPage() {
  const [baseUrl, setBaseUrl] = useState(DEFAULT_API_BASE_URL);
  const [apiKey, setApiKey] = useState("");
  const [revealed, setRevealed] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [submitting, setSubmitting] = useState(false);

  const canSubmit = baseUrl.trim().length > 0 && apiKey.trim().length > 0 && !submitting;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    const normalized = normalizeBaseUrl(baseUrl);
    try {
      await verifyCredentials(normalized, apiKey.trim());
      setSession(normalized, apiKey.trim());
      setApiKey("");
    } catch (caught) {
      setError(caught);
    } finally {
      setSubmitting(false);
    }
  }

  function handleClear() {
    setApiKey("");
    setBaseUrl(DEFAULT_API_BASE_URL);
    setError(null);
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
            AI Footprint
          </p>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight">Connect to AI Footprint</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Enter your developer API key to connect this console to your AI Footprint
            organization.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-5 rounded-[var(--radius-console)] border border-border bg-surface p-6"
        >
          <Field
            label="API Base URL"
            htmlFor="api-base-url"
            hint="For example https://api.example.com — the console appends /v1 itself."
          >
            <Input
              id="api-base-url"
              name="apiBaseUrl"
              type="url"
              inputMode="url"
              autoComplete="off"
              placeholder="https://api.example.com"
              value={baseUrl}
              onChange={(event) => setBaseUrl(event.target.value)}
              required
            />
          </Field>

          <Field
            label="API Key"
            htmlFor="api-key"
            hint="Kept in this browser tab's sessionStorage only, and sent as a bearer token."
          >
            <div className="relative">
              <Input
                id="api-key"
                name="apiKey"
                type={revealed ? "text" : "password"}
                autoComplete="off"
                spellCheck={false}
                placeholder="afp_live_..."
                className="pr-10 font-mono"
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setRevealed((value) => !value)}
                aria-label={revealed ? "Hide API key" : "Show API key"}
                className="absolute right-1 top-1 rounded p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                {revealed ? (
                  <EyeOff className="h-4 w-4" aria-hidden="true" />
                ) : (
                  <Eye className="h-4 w-4" aria-hidden="true" />
                )}
              </button>
            </div>
          </Field>

          <InlineError error={error} />

          <div className="flex gap-2">
            <Button type="submit" disabled={!canSubmit} className="flex-1">
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  Connecting
                </>
              ) : (
                "Connect"
              )}
            </Button>
            <Button type="button" variant="secondary" onClick={handleClear} disabled={submitting}>
              Clear
            </Button>
          </div>
        </form>

        <p className="mt-4 text-center text-xs text-muted-foreground">
          AI Footprint reports estimated resource impact as ranges with confidence, coverage and
          methodology provenance — never as exact measurements.
        </p>
      </div>
    </main>
  );
}
