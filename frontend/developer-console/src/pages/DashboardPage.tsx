import { Link } from "react-router-dom";

import { ErrorState } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CardsSkeleton, Skeleton } from "@/components/ui/skeleton";
import { useApiKeys, useApplications, useOrganization, useProjects } from "@/hooks/queries";

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

  const organizationId = projects.data?.items[0]?.organization_id;
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
              Organization details become available once this organization has at least one
              project.
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
          <CardTitle>Recent activity</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No workload data yet. Workload and estimate views arrive with the Usage section; this
            console never displays activity that did not come from the API.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button asChild variant="secondary" size="sm">
              <Link to="/projects">View projects</Link>
            </Button>
            <Button asChild variant="secondary" size="sm">
              <Link to="/applications">View applications</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
