import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { describeError } from "@/lib/errors/apiError";

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const { message, requestId } = describeError(error);
  return (
    <div
      role="alert"
      className="rounded-[var(--radius-console)] border border-danger/40 bg-danger/5 px-5 py-4"
    >
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-danger" aria-hidden="true" />
        <div className="space-y-1">
          <p className="text-sm font-medium text-foreground">{message}</p>
          {requestId ? (
            <p className="font-mono text-xs text-muted-foreground">Request ID: {requestId}</p>
          ) : null}
          {onRetry ? (
            <Button variant="secondary" size="sm" className="mt-2" onClick={onRetry}>
              Try again
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export function InlineError({ error }: { error: unknown }) {
  if (!error) return null;
  const { message, requestId } = describeError(error);
  return (
    <div role="alert" className="space-y-1 rounded border border-danger/40 bg-danger/5 px-3 py-2">
      <p className="text-sm text-foreground">{message}</p>
      {requestId ? (
        <p className="font-mono text-xs text-muted-foreground">Request ID: {requestId}</p>
      ) : null}
    </div>
  );
}
