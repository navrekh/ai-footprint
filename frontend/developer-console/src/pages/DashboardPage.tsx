import { Link } from "react-router-dom";

import { ErrorState } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CardsSkeleton, Skeleton } from "@/components/ui/skeleton";
import {
  useApiKeys,
  useApplications,
  useConnectedApiKey,
  useOrganization,
  useProjects,
} from "@/hooks/queries";

function Metric({
  label,
  value,
  sublabel,
  loading,
}: {
  label: string;
  value: number | string;
  sublabel?: string;
  loading?: boolean;
}) {
  return (
    <div className="rounded-[var(--radius-console)] border border-border bg-surface p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      {loading ? (
        <Skeleton className="mt-3 h-7 w-16" />
      ) : (
        <p className="mt-2 text-2xl font-semibold tabular-nums">{value}</p>
      )}
      {sublabel && !loading ? (
        <p className="mt-1 text-xs text-muted-foreground">{sublabel}</p>
      ) : null}
    </div>
  );
}

export function DashboardPage() {
  const projects = useProjects();
  const applications = useApplications();
  const apiKeys = useApiKeys();
  const connected = useConnectedApiKey();

  /**
   * Organization identity comes from the connected key's own metadata
   * (GET /v1/api-keys exposes organization_id as non-secret metadata — see
   * lib/auth/connectedKey.ts), so an organization with zero projects still
   * resolves. Fallback: the first project's organization_id, kept for the
   * case where the connected key cannot be identified (documented API
   * limitation: no endpoint returns the authenticated key's identity). An
   * organization ID is never fabricated — if neither source yields one,
   * the card below explains the limitation instead of rendering data.
   */
  const organizationId =
    connected.connected?.organization_id ?? projects.data?.items[0]?.organization_id;
  const organization = useOrganization(organizationId);

  const error = projects.error ?? applications.error ?? apiKeys.error;
  const loading = projects.isPending || applications.isPending || apiKeys.isPending;

  const activeProjects = projects.data?.items.filter((p) => p.status === "active").length ?? 0;
  const activeApplications =
    applications.data?.items.filter((a) => a.status === "active").length ?? 0;
  const activeKeys = apiKeys.data?.items.filter((k) => k.status === "active").length ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Organization overview for the API key this console is connected with."
      />

      {error ? (
        <ErrorState
          error={error}
          onRetry={() => {
            projects.refetch();
            applications.refetch();
            apiKeys.refetch();
          }}
        />
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Organization</CardTitle>
        </CardHeader>
        <CardContent>
          {organization.isPending && organizationId ? (
            <div className="space-y-2">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-4 w-32" />
            </div>
          ) : organization.data ? (
            <dl className="grid gap-4 sm:grid-cols-3">
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">Name</dt>
                <dd className="mt-1 text-sm font-medium">{organization.data.name}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">Slug</dt>
                <dd className="mt-1 font-mono text-sm">{organization.data.slug}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">Status</dt>
                <dd className="mt-1">
                  <StatusBadge status={organization.data.status} />
                </dd>
              </div>
            </dl>
          ) : (
            <p className="text-sm text-muted-foreground">
              Organization details are unavailable: the connected key could not be identified
              from key metadata and this organization has no projects yet. The console does not
              fabricate organization identity.
            </p>
          )}
        </CardContent>
      </Card>

      {loading ? (
        <CardsSkeleton count={4} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Metric
            label="Projects"
            value={projects.data?.total ?? 0}
            sublabel={`${activeProjects} active`}
          />
          <Metric
            label="Applications"
            value={applications.data?.total ?? 0}
            sublabel={`${activeApplications} active`}
          />
          <Metric
            label="API keys"
            value={apiKeys.data?.total ?? 0}
            sublabel={`${activeKeys} active`}
          />
          <Metric
            label="Methodology"
            value="Estimates"
            sublabel="Ranges with confidence and coverage"
          />
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Explore your resource intelligence</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Understand what your workload looks like — estimated resource ranges, coverage and
            confidence, sourced directly from the API. This console never fabricates or
            recommends; it only shows what the backend reports.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button asChild variant="secondary" size="sm">
              <Link to="/projects">View projects</Link>
            </Button>
            <Button asChild variant="secondary" size="sm">
              <Link to="/applications">View applications</Link>
            </Button>
            <Button asChild variant="secondary" size="sm">
              <Link to="/usage">View usage</Link>
            </Button>
            <Button asChild variant="secondary" size="sm">
              <Link to="/compare">Compare workloads</Link>
            </Button>
            <Button asChild variant="secondary" size="sm">
              <Link to="/benchmarks">Browse benchmarks</Link>
            </Button>
            <Button asChild variant="secondary" size="sm">
              <Link to="/api-explorer">Open API Explorer</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
