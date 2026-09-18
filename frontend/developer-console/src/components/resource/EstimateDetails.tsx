import type { EstimateResponse } from "@/types/api";

/**
 * "Where did this number come from?" — an expandable panel rather than
 * cluttering the main view. Renders only fields present on this specific
 * estimate response (confidence, evidence level, accounting boundary,
 * methodology version, assumptions). The compare/benchmark-run contract
 * does not include limitations or source provenance on the estimate
 * itself — a separate GET /v1/methodology registry has those fields for
 * some versions, but joining it in here would show information that
 * isn't actually part of this response, so this panel deliberately does
 * not do that join. Nothing here is authored in the frontend.
 */
export function EstimateDetails({ estimate }: { estimate: EstimateResponse }) {
  return (
    <details className="group rounded-[var(--radius-console)] border border-border bg-surface-raised/50">
      <summary className="cursor-pointer select-none px-4 py-2.5 text-sm font-medium text-foreground marker:content-none">
        <span className="inline-flex items-center gap-1.5">
           Methodology &amp; response details
          <span className="text-xs font-normal text-muted-foreground group-open:hidden">
            (show)
          </span>
          <span className="hidden text-xs font-normal text-muted-foreground group-open:inline">
            (hide)
          </span>
        </span>
      </summary>
      <div className="space-y-3 border-t border-border px-4 py-3 text-sm">
        <dl className="grid gap-3 sm:grid-cols-2">
          <div>
            <dt className="text-xs uppercase tracking-wide text-muted-foreground">Confidence</dt>
             <dd className="mt-0.5">{estimate.confidence ?? "Not available in this response"}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-muted-foreground">
              Evidence level
            </dt>
             <dd className="mt-0.5">{estimate.evidence_level ?? "Not available in this response"}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-muted-foreground">
              Accounting boundary
            </dt>
             <dd className="mt-0.5">{estimate.accounting_boundary ?? "Not available in this response"}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-muted-foreground">
              Methodology version
            </dt>
             <dd className="mt-0.5 font-mono text-xs">{estimate.methodology_version ?? "Not available in this response"}</dd>
          </div>
        </dl>

        {estimate.assumptions.length > 0 ? (
          <div>
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Assumptions</p>
            <ul className="mt-1 list-disc space-y-0.5 pl-4 text-sm text-foreground">
              {estimate.assumptions.map((assumption) => (
                <li key={assumption}>{assumption}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <p className="text-xs text-muted-foreground">
          Limitations and source provenance are not included in this response.
        </p>
      </div>
    </details>
  );
}
