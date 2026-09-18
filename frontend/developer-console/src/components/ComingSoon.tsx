import { PageHeader } from "@/components/PageHeader";

/**
 * Placeholder for sections landing in Sprint 5D. It intentionally shows no
 * numbers: the console never renders resource-impact values that did not
 * come from the API.
 */
export function ComingSoon({
  title,
  description,
  capabilities,
}: {
  title: string;
  description: string;
  capabilities: string[];
}) {
  return (
    <div className="space-y-6">
      <PageHeader title={title} description={description} />
      <div className="rounded-[var(--radius-console)] border border-dashed border-border bg-surface px-6 py-10">
        <p className="text-sm font-medium text-foreground">Coming soon</p>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          This section is not part of the Developer Console foundation. It will read from the
          existing AI Footprint API in a later sprint.
        </p>
        <ul className="mt-4 space-y-1.5 text-sm text-muted-foreground">
          {capabilities.map((item) => (
            <li key={item} className="flex gap-2">
              <span aria-hidden="true">·</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
