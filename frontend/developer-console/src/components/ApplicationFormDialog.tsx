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
import {
  useConnectedApiKey,
  useCreateApplication,
  useProjects,
  useUpdateApplication,
} from "@/hooks/queries";
import { resolveConnectedKeyScope } from "@/lib/auth/connectedKey";
import type { Application, ApplicationEnvironment, ApplicationStatus } from "@/types/api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  application?: Application;
  /**
   * The project a caller opened this dialog from (e.g. a project detail
   * page). Deliberately NOT used to pre-fill or pre-select the project
   * field for a new application: doing so let a stale/contextual value
   * silently satisfy the "explicit project selection" requirement for an
   * organization-level or unidentifiable credential, without the user
   * ever actually choosing it. A project-scoped credential ignores this
   * value entirely regardless (it is always locked to its own project -
   * see `scope.kind === "project"` below).
   */
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
  const connected = useConnectedApiKey();
  const scope = resolveConnectedKeyScope(connected.connected);

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
    // For a new application, the project field always starts empty (never
    // seeded from `defaultProjectId`) - see the Props doc comment above:
    // a contextual/default value must never silently satisfy the explicit
    // selection requirement below. Editing always has a real project_id.
    setProjectId(application?.project_id ?? "");
    create.reset();
    update.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, application]);

  const lockedProjectName =
    scope.kind === "project"
      ? (projects.data?.items.find((project) => project.id === scope.projectId)?.name ??
        scope.projectId)
      : null;

  // Display-only context (e.g. "opened from Mobile's page") for a
  // non-locked scope - never used to pre-fill `projectId` or otherwise
  // treated as an explicit selection. See the Props doc comment above.
  const defaultProjectName =
    scope.kind !== "project" && defaultProjectId
      ? (projects.data?.items.find((project) => project.id === defaultProjectId)?.name ??
        defaultProjectId)
      : null;

  /**
   * Scope handling mirrors ApiKeysPage.tsx / lib/auth/connectedKey.ts:
   * - project-scoped credential: locked to its own project - the locked
   *   scope wins over any stale form state (a different project's
   *   defaultProjectId, or a leftover selection), exactly as for API key
   *   creation;
   * - organization-level or unidentifiable ("unknown") credential: an
   *   explicit project is always required. Unlike API key creation,
   *   applications have no "organization-level" concept to fall back to,
   *   so both cases behave the same way here - there is nothing safe to
   *   imply from a blank selection either way.
   */
  const canSubmit =
    name.trim().length > 0 &&
    !pending &&
    !connected.isPending &&
    (isEdit || scope.kind === "project" || projectId !== "");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) return;
    try {
      if (application) {
        await update.mutateAsync({
          name: name.trim(),
          description: description.trim() || null,
          status,
          environment: environment || null,
        });
      } else {
        const effectiveProjectId = scope.kind === "project" ? scope.projectId : projectId;
        if (!effectiveProjectId) return;
        await create.mutateAsync({
          name: name.trim(),
          description: description.trim() || null,
          environment: environment || null,
          project_id: effectiveProjectId,
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

          {!isEdit && scope.kind === "project" ? (
            <Field
              label="Project"
              htmlFor="application-project-locked"
              hint="The connected key is scoped to this project; applications created here belong to it."
            >
              <Input
                id="application-project-locked"
                value={lockedProjectName ?? ""}
                disabled
                readOnly
              />
            </Field>
          ) : !isEdit ? (
            <Field
              label="Project"
              htmlFor="application-project"
              hint={
                (scope.kind === "organization"
                  ? "Required. Applications always belong to exactly one project."
                  : "The console could not determine the connected key's scope, so an explicit project is required.") +
                (defaultProjectName ? ` Opened from ${defaultProjectName} - select it explicitly to use it.` : "")
              }
            >
              <Select
                id="application-project"
                value={projectId}
                required
                onChange={(event) => setProjectId(event.target.value)}
              >
                <option value="" disabled>
                  Select a project…
                </option>
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
            <Button type="submit" disabled={!canSubmit}>
              {pending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
              {isEdit ? "Save changes" : "Create application"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
