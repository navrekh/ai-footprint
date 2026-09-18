import { useState } from "react";
import { Plus } from "lucide-react";

import { ApplicationFormDialog } from "@/components/ApplicationFormDialog";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Select } from "@/components/ui/field";
import { TableSkeleton } from "@/components/ui/skeleton";
import { Table, TableWrapper, Td, Th } from "@/components/ui/table";
import { useApplications, useProjects } from "@/hooks/queries";
import { formatDateTime } from "@/lib/utils/format";
import type { Application } from "@/types/api";

export function ApplicationsPage() {
  const [projectFilter, setProjectFilter] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<Application | undefined>(undefined);

  const projects = useProjects();
  const applications = useApplications(projectFilter || null);

  const projectName = (id: string) =>
    projects.data?.items.find((project) => project.id === id)?.name ?? id;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Applications"
        description="AI products, clients and environments that generate workloads."
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" aria-hidden="true" />
            Create Application
          </Button>
        }
      />

      <div className="max-w-xs">
        <Field label="Filter by project" htmlFor="application-project-filter">
          <Select
            id="application-project-filter"
            value={projectFilter}
            onChange={(event) => setProjectFilter(event.target.value)}
          >
            <option value="">All projects</option>
            {projects.data?.items.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </Select>
        </Field>
      </div>

      {applications.isPending ? (
        <TableSkeleton rows={4} columns={5} />
      ) : applications.error ? (
        <ErrorState error={applications.error} onRetry={() => applications.refetch()} />
      ) : applications.data.items.length === 0 ? (
        <EmptyState
          title="No applications yet"
          description="Applications represent the AI products or environments generating workloads."
          action={<Button onClick={() => setCreateOpen(true)}>Create Application</Button>}
        />
      ) : (
        <TableWrapper>
          <Table>
            <caption className="sr-only">Applications visible to this API key</caption>
            <thead>
              <tr>
                <Th>Name</Th>
                <Th>Project</Th>
                <Th>Environment</Th>
                <Th>Status</Th>
                <Th>Created</Th>
                <Th><span className="sr-only">Actions</span></Th>
              </tr>
            </thead>
            <tbody>
              {applications.data.items.map((application) => (
                <tr key={application.id} className="last:[&>td]:border-b-0">
                  <Td>
                    <span className="font-medium">{application.name}</span>
                    <p className="font-mono text-xs text-muted-foreground">{application.slug}</p>
                  </Td>
                  <Td className="text-muted-foreground">{projectName(application.project_id)}</Td>
                  <Td className="text-muted-foreground">{application.environment ?? "—"}</Td>
                  <Td>
                    <StatusBadge status={application.status} />
                  </Td>
                  <Td className="text-muted-foreground">
                    {formatDateTime(application.created_at)}
                  </Td>
                  <Td className="text-right">
                    <Button variant="secondary" size="sm" onClick={() => setEditing(application)}>
                      Edit
                    </Button>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </TableWrapper>
      )}

      <ApplicationFormDialog open={createOpen} onOpenChange={setCreateOpen} />
      <ApplicationFormDialog
        open={Boolean(editing)}
        onOpenChange={(open) => {
          if (!open) setEditing(undefined);
        }}
        application={editing}
      />
    </div>
  );
}
