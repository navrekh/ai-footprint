import { useEffect, useState, type FormEvent } from "react";
import { Loader2 } from "lucide-react";

import { InlineError } from "@/components/ErrorState";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { useCreateApplication, useProjects, useUpdateApplication } from "@/hooks/queries";
import type { Application, ApplicationEnvironment, ApplicationStatus } from "@/types/api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  application?: Application;
  /** Pre-selected project when creating from a project detail page. */
  defaultProjectId?: string;
}

const ENVIRONMENTS: ApplicationEnvironment[] = ["development", "staging", "production"];

export function ApplicationFormDialog({
  open,
  onOpenChange,
  application,
  defaultProjectId,
}: Props) {
  const isEdit = Boolean(application);
  const projects = useProjects();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [environment, setEnvironment] = useState<"" | ApplicationEnvironment>("");
  const [projectId, setProjectId] = useState("");
  const [status, setStatus] = useState<ApplicationStatus>("active");

  const create = useCreateApplication();
  const update = useUpdateApplication(application?.id ?? "");
  const pending = create.isPending || update.isPending;
  const error = create.error ?? update.error;

  useEffect(() => {
    if (!open) return;
    setName(application?.name ?? "");
    setDescription(application?.description ?? "");
    setEnvironment((application?.environment as ApplicationEnvironment) ?? "");
    setStatus((application?.status as ApplicationStatus) ?? "active");
    setProjectId(application?.project_id ?? defaultProjectId ?? "");
    create.reset();
    update.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, application, defaultProjectId]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim() || pending) return;
    try {
      if (application) {
        await update.mutateAsync({
          name: name.trim(),
          description: description.trim() || null,
          status,
          environment: environment || null,
        });
      } else {
        await create.mutateAsync({
          name: name.trim(),
          description: description.trim() || null,
          environment: environment || null,
          project_id: projectId || null,
        });
      }
      onOpenChange(false);
    } catch {
      /* error surfaced through the mutation state */
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit application" : "Create application"}</DialogTitle>
          <DialogDescription>
            Applications represent the AI products or environments generating workloads.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label="Name" htmlFor="application-name">
            <Input
              id="application-name"
              value={name}
              maxLength={255}
              required
              onChange={(event) => setName(event.target.value)}
            />
          </Field>

          {!isEdit ? (
            <Field
              label="Project"
              htmlFor="application-project"
              hint="Required when connected with an organization-level API key; a project-scoped key targets its own project."
            >
              <Select
                id="application-project"
                value={projectId}
                onChange={(event) => setProjectId(event.target.value)}
              >
                <option value="">Use the API key's own project</option>
                {projects.data?.items.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </Select>
            </Field>
          ) : null}

          <Field label="Environment" htmlFor="application-environment" hint="Optional.">
            <Select
              id="application-environment"
              value={environment}
              onChange={(event) =>
                setEnvironment(event.target.value as "" | ApplicationEnvironment)
              }
            >
              <option value="">Not set</option>
              {ENVIRONMENTS.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </Select>
          </Field>

          <Field label="Description" htmlFor="application-description" hint="Optional.">
            <Textarea
              id="application-description"
              value={description}
              maxLength={2000}
              onChange={(event) => setDescription(event.target.value)}
            />
          </Field>

          {isEdit ? (
            <Field label="Status" htmlFor="application-status">
              <Select
                id="application-status"
                value={status}
                onChange={(event) => setStatus(event.target.value as ApplicationStatus)}
              >
                <option value="active">active</option>
                <option value="inactive">inactive</option>
              </Select>
            </Field>
          ) : null}

          <InlineError error={error} />

          <DialogFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => onOpenChange(false)}
              disabled={pending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={pending || !name.trim()}>
              {pending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
              {isEdit ? "Save changes" : "Create application"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
