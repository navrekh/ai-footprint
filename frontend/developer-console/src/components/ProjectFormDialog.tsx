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
import { useCreateProject, useUpdateProject } from "@/hooks/queries";
import type { Project, ProjectStatus } from "@/types/api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  project?: Project;
  onCreated?: (project: Project) => void;
}

export function ProjectFormDialog({ open, onOpenChange, project, onCreated }: Props) {
  const isEdit = Boolean(project);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<ProjectStatus>("active");

  const create = useCreateProject();
  const update = useUpdateProject(project?.id ?? "");
  const pending = create.isPending || update.isPending;
  const error = create.error ?? update.error;

  useEffect(() => {
    if (!open) return;
    setName(project?.name ?? "");
    setDescription(project?.description ?? "");
    setStatus((project?.status as ProjectStatus) ?? "active");
    create.reset();
    update.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, project]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim() || pending) return;
    try {
      if (project) {
        await update.mutateAsync({
          name: name.trim(),
          description: description.trim() || null,
          status,
        });
      } else {
        const created = await create.mutateAsync({
          name: name.trim(),
          description: description.trim() || null,
        });
        onCreated?.(created);
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
          <DialogTitle>{isEdit ? "Edit project" : "Create project"}</DialogTitle>
          <DialogDescription>
            Projects group the applications and workloads of your organization.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label="Name" htmlFor="project-name">
            <Input
              id="project-name"
              value={name}
              maxLength={255}
              required
              onChange={(event) => setName(event.target.value)}
            />
          </Field>

          <Field label="Description" htmlFor="project-description" hint="Optional.">
            <Textarea
              id="project-description"
              value={description}
              maxLength={2000}
              onChange={(event) => setDescription(event.target.value)}
            />
          </Field>

          {isEdit ? (
            <Field label="Status" htmlFor="project-status">
              <Select
                id="project-status"
                value={status}
                onChange={(event) => setStatus(event.target.value as ProjectStatus)}
              >
                <option value="active">active</option>
                <option value="archived">archived</option>
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
              {isEdit ? "Save changes" : "Create project"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
