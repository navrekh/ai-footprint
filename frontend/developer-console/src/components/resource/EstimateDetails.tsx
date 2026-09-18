import { useMethodology } from "@/hooks/queries";
import type { EstimateResponse } from "@/types/api";

/**
 * "Where did this number come from?" — an expandable panel rather than
 * cluttering the main view. Renders only what the API actually returned:
 * the estimate's own confidence/evidence/assumptions, cross-referenced
 * against GET /v1/methodology (by methodology_version) for the published
 * sources/limitations text. Nothing here is authored in the frontend.
 */
export function EstimateDetails({ estimate }: { estimate: EstimateResponse }) {
  const methodology = useMethodology();
  const published = methodology.data?.find((m) => m.version === estimate.methodology_version);

  return (
    <details className="group rounded-[var(--radius-console)] border border-border bg-surface-raised/50">
      <summary className="cursor-pointer select-none px-4 py-2.5 text-sm font-medium text-foreground marker:content-none">
        <span className="inline-flex items-center gap-1.5">
          Methodology &amp; provenance
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
            <dd className="mt-0.5">{estimate.confidence ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-muted-foreground">
              Evidence level
            </dt>
            <dd className="mt-0.5">{estimate.evidence_level ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-muted-foreground">
              Accounting boundary
            </dt>
            <dd className="mt-0.5">{estimate.accounting_boundary ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-muted-foreground">
              Methodology version
            </dt>
            <dd className="mt-0.5 font-mono text-xs">{estimate.methodology_version ?? "—"}</dd>
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

        {published ? (
          <>
            {published.limitations.length > 0 ? (
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">
                  Limitations
                </p>
                <ul className="mt-1 list-disc space-y-0.5 pl-4 text-sm text-foreground">
                  {published.limitations.map((limitation) => (
                    <li key={limitation}>{limitation}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {published.sources.length > 0 ? (
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Sources</p>
                <ul className="mt-1 list-disc space-y-0.5 pl-4 text-sm text-foreground">
                  {published.sources.map((source) => (
                    <li key={source} className="break-all">
                      {source}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </>
        ) : methodology.isPending ? (
          <p className="text-xs text-muted-foreground">Loading published methodology…</p>
        ) : null}
      </div>
    </details>
  );
}
