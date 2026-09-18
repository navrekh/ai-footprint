import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Plus } from "lucide-react";

import { ApplicationFormDialog } from "@/components/ApplicationFormDialog";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { ProjectFormDialog } from "@/components/ProjectFormDialog";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton, TableSkeleton } from "@/components/ui/skeleton";
import { Table, TableWrapper, Td, Th } from "@/components/ui/table";
import { useApplications, useProject } from "@/hooks/queries";
import { formatDateTime } from "@/lib/utils/format";

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const project = useProject(projectId);
  // Scoped to this project only — never shows another project's data.
  const applications = useApplications(projectId ?? null);

  const [editOpen, setEditOpen] = useState(false);
  const [createAppOpen, setCreateAppOpen] = useState(false);

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link to="/projects">
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to projects
        </Link>
      </Button>

      {project.isPending ? (
        <Skeleton className="h-8 w-64" />
      ) : project.error ? (
        <ErrorState error={project.error} onRetry={() => project.refetch()} />
      ) : (
        <>
          <PageHeader
            title={project.data.name}
            description={project.data.description ?? undefined}
            actions={
              <>
                <Button variant="secondary" onClick={() => setEditOpen(true)}>
                  Edit Project
                </Button>
                <Button onClick={() => setCreateAppOpen(true)}>
                  <Plus className="h-4 w-4" aria-hidden="true" />
                  Create Application
                </Button>
              </>
            }
          />

          <Card>
            <CardHeader className="flex items-center justify-between gap-3">
              <CardTitle>Project</CardTitle>
              <Button asChild variant="ghost" size="sm">
                <Link to="/api-keys">View API Keys</Link>
              </Button>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <dt className="text-xs uppercase tracking-wide text-muted-foreground">Slug</dt>
                  <dd className="mt-1 font-mono text-sm">{project.data.slug}</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide text-muted-foreground">Status</dt>
                  <dd className="mt-1">
                    <StatusBadge status={project.data.status} />
                  </dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                    Project ID
                  </dt>
                  <dd className="mt-1 font-mono text-xs break-all">{project.data.id}</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide text-muted-foreground">Updated</dt>
                  <dd className="mt-1 text-sm">{formatDateTime(project.data.updated_at)}</dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <section className="space-y-3">
            <h2 className="text-sm font-semibold">Applications</h2>
            {applications.isPending ? (
              <TableSkeleton rows={3} columns={4} />
            ) : applications.error ? (
              <ErrorState error={applications.error} onRetry={() => applications.refetch()} />
            ) : applications.data.items.length === 0 ? (
              <EmptyState
                title="No applications yet"
                description="Applications represent the AI products or environments generating workloads."
                action={
                  <Button onClick={() => setCreateAppOpen(true)}>Create Application</Button>
                }
              />
            ) : (
              <TableWrapper>
                <Table>
                  <caption className="sr-only">Applications in this project</caption>
                  <thead>
                    <tr>
                      <Th>Name</Th>
                      <Th>Environment</Th>
                      <Th>Status</Th>
                      <Th>Created</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {applications.data.items.map((application) => (
                      <tr key={application.id} className="last:[&>td]:border-b-0">
                        <Td>
                          <span className="font-medium">{application.name}</span>
                          <p className="font-mono text-xs text-muted-foreground">
                            {application.slug}
                          </p>
                        </Td>
                        <Td className="text-muted-foreground">{application.environment ?? "—"}</Td>
                        <Td>
                          <StatusBadge status={application.status} />
                        </Td>
                        <Td className="text-muted-foreground">
                          {formatDateTime(application.created_at)}
                        </Td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </TableWrapper>
            )}
          </section>

          <ProjectFormDialog
            open={editOpen}
            onOpenChange={setEditOpen}
            project={project.data}
          />
          <ApplicationFormDialog
            open={createAppOpen}
            onOpenChange={setCreateAppOpen}
            defaultProjectId={project.data.id}
          />
        </>
      )}
    </div>
  );
}
