import { useState } from "react";
import { Link } from "react-router-dom";
import { Plus } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { ProjectFormDialog } from "@/components/ProjectFormDialog";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableWrapper, Td, Th } from "@/components/ui/table";
import { TableSkeleton } from "@/components/ui/skeleton";
import { useProjects } from "@/hooks/queries";
import { formatDate } from "@/lib/utils/format";

export function ProjectsPage() {
  const projects = useProjects();
  const [createOpen, setCreateOpen] = useState(false);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Projects"
        description="Projects group applications and workloads within your organization."
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" aria-hidden="true" />
            Create Project
          </Button>
        }
      />

      {projects.isPending ? (
        <TableSkeleton rows={4} columns={5} />
      ) : projects.error ? (
        <ErrorState error={projects.error} onRetry={() => projects.refetch()} />
      ) : projects.data.items.length === 0 ? (
        <EmptyState
          title="No projects yet"
          description="Create your first project to start organizing AI workloads."
          action={<Button onClick={() => setCreateOpen(true)}>Create Project</Button>}
        />
      ) : (
        <TableWrapper>
          <Table>
            <caption className="sr-only">Projects in this organization</caption>
            <thead>
              <tr>
                <Th>Name</Th>
                <Th>Slug</Th>
                <Th>Status</Th>
                <Th>Created</Th>
                <Th><span className="sr-only">Actions</span></Th>
              </tr>
            </thead>
            <tbody>
              {projects.data.items.map((project) => (
                <tr key={project.id} className="last:[&>td]:border-b-0">
                  <Td>
                    <Link
                      to={`/projects/${project.id}`}
                      className="font-medium text-foreground hover:text-primary hover:underline"
                    >
                      {project.name}
                    </Link>
                    {project.description ? (
                      <p className="mt-0.5 max-w-md truncate text-xs text-muted-foreground">
                        {project.description}
                      </p>
                    ) : null}
                  </Td>
                  <Td className="font-mono text-xs text-muted-foreground">{project.slug}</Td>
                  <Td>
                    <StatusBadge status={project.status} />
                  </Td>
                  <Td className="text-muted-foreground">{formatDate(project.created_at)}</Td>
                  <Td className="text-right">
                    <Button asChild variant="secondary" size="sm">
                      <Link to={`/projects/${project.id}`}>Open Project</Link>
                    </Button>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </TableWrapper>
      )}

      <ProjectFormDialog open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  );
}
