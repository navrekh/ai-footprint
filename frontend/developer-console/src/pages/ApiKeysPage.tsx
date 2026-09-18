import { useState, type FormEvent } from "react";
import { Check, Copy, Loader2, Plus } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { ErrorState, InlineError } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Field, Input, Select } from "@/components/ui/field";
import { TableSkeleton } from "@/components/ui/skeleton";
import { Table, TableWrapper, Td, Th } from "@/components/ui/table";
import { useApiKeys, useCreateApiKey, useProjects, useRevokeApiKey } from "@/hooks/queries";
import { formatDateTime } from "@/lib/utils/format";
import type { ApiKey, ApiKeyCreated } from "@/types/api";

export function ApiKeysPage() {
  const keys = useApiKeys();
  const projects = useProjects();
  const [createOpen, setCreateOpen] = useState(false);
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);
  const [revoking, setRevoking] = useState<ApiKey | null>(null);

  const projectLabel = (id: string | null) => {
    if (!id) return "Organization-level";
    return projects.data?.items.find((project) => project.id === id)?.name ?? id;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="API Keys"
        description="Keys authenticate your applications against the AI Footprint API. Only key metadata is ever stored or shown here."
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" aria-hidden="true" />
            Create API Key
          </Button>
        }
      />

      {keys.isPending ? (
        <TableSkeleton rows={4} columns={6} />
      ) : keys.error ? (
        <ErrorState error={keys.error} onRetry={() => keys.refetch()} />
      ) : keys.data.items.length === 0 ? (
        <EmptyState
          title="No API keys yet"
          description="Create an API key to connect your application to AI Footprint."
          action={<Button onClick={() => setCreateOpen(true)}>Create API Key</Button>}
        />
      ) : (
        <TableWrapper>
          <Table>
            <caption className="sr-only">API keys in this organization</caption>
            <thead>
              <tr>
                <Th>Name</Th>
                <Th>Key prefix</Th>
                <Th>Scope</Th>
                <Th>Status</Th>
                <Th>Created</Th>
                <Th>Expires</Th>
                <Th>Last used</Th>
                <Th><span className="sr-only">Actions</span></Th>
              </tr>
            </thead>
            <tbody>
              {keys.data.items.map((key) => (
                <tr key={key.id} className="last:[&>td]:border-b-0">
                  <Td className="font-medium">{key.name}</Td>
                  <Td className="font-mono text-xs text-muted-foreground">{key.key_prefix}…</Td>
                  <Td className="text-muted-foreground">{projectLabel(key.project_id)}</Td>
                  <Td>
                    <StatusBadge status={key.status} />
                  </Td>
                  <Td className="text-muted-foreground">{formatDateTime(key.created_at)}</Td>
                  <Td className="text-muted-foreground">{formatDateTime(key.expires_at)}</Td>
                  <Td className="text-muted-foreground">{formatDateTime(key.last_used_at)}</Td>
                  <Td className="text-right">
                    {key.status === "active" ? (
                      <Button variant="secondary" size="sm" onClick={() => setRevoking(key)}>
                        Revoke
                      </Button>
                    ) : (
                      <span className="text-xs text-muted-foreground">
                        Revoked {formatDateTime(key.revoked_at)}
                      </span>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </TableWrapper>
      )}

      <CreateApiKeyDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onCreated={(created) => setCreatedKey(created)}
      />
      <RawKeyDialog created={createdKey} onDone={() => setCreatedKey(null)} />
      <RevokeDialog apiKey={revoking} onClose={() => setRevoking(null)} />
    </div>
  );
}

function CreateApiKeyDialog({
  open,
  onOpenChange,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: (created: ApiKeyCreated) => void;
}) {
  const [name, setName] = useState("");
  const [projectId, setProjectId] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const projects = useProjects();
  const create = useCreateApiKey();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim() || create.isPending) return;
    try {
      const created = await create.mutateAsync({
        name: name.trim(),
        project_id: projectId || null,
        expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
      });
      setName("");
      setProjectId("");
      setExpiresAt("");
      onOpenChange(false);
      onCreated(created);
    } catch {
      /* error surfaced through the mutation state */
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create API key</DialogTitle>
          <DialogDescription>
            The raw key is returned by the API once, at creation time, and cannot be retrieved
            afterwards.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label="Name" htmlFor="api-key-name">
            <Input
              id="api-key-name"
              value={name}
              maxLength={255}
              required
              onChange={(event) => setName(event.target.value)}
            />
          </Field>

          <Field
            label="Scope"
            htmlFor="api-key-project"
            hint="Scope the key to one project, or leave organization-level."
          >
            <Select
              id="api-key-project"
              value={projectId}
              onChange={(event) => setProjectId(event.target.value)}
            >
              <option value="">Organization-level</option>
              {projects.data?.items.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </Select>
          </Field>

          <Field label="Expires at" htmlFor="api-key-expires" hint="Optional.">
            <Input
              id="api-key-expires"
              type="datetime-local"
              value={expiresAt}
              onChange={(event) => setExpiresAt(event.target.value)}
            />
          </Field>

          <InlineError error={create.error} />

          <DialogFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => onOpenChange(false)}
              disabled={create.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={create.isPending || !name.trim()}>
              {create.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : null}
              Create API Key
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

/**
 * One-time display of raw key material. The value lives in component state
 * for the lifetime of this dialog only — it is never stored, re-fetched or
 * rendered again once dismissed.
 */
function RawKeyDialog({
  created,
  onDone,
}: {
  created: ApiKeyCreated | null;
  onDone: () => void;
}) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    if (!created) return;
    try {
      await navigator.clipboard.writeText(created.key);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <Dialog
      open={Boolean(created)}
      onOpenChange={(open) => {
        if (!open) {
          setCopied(false);
          onDone();
        }
      }}
    >
      <DialogContent showClose={false}>
        <DialogHeader>
          <DialogTitle>Your API key is shown once</DialogTitle>
          <DialogDescription>
            Your API key is shown once. Copy it now and store it securely.
          </DialogDescription>
        </DialogHeader>

        {created ? (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              {created.name} · prefix <span className="font-mono">{created.key_prefix}</span>
            </p>
            <code className="block w-full break-all rounded-[var(--radius-console)] border border-border bg-input px-3 py-3 font-mono text-sm">
              {created.key}
            </code>
          </div>
        ) : null}

        <DialogFooter>
          <Button variant="secondary" onClick={handleCopy}>
            {copied ? (
              <Check className="h-4 w-4" aria-hidden="true" />
            ) : (
              <Copy className="h-4 w-4" aria-hidden="true" />
            )}
            {copied ? "Copied" : "Copy"}
          </Button>
          <Button
            onClick={() => {
              setCopied(false);
              onDone();
            }}
          >
            Done
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function RevokeDialog({ apiKey, onClose }: { apiKey: ApiKey | null; onClose: () => void }) {
  const revoke = useRevokeApiKey();

  async function handleRevoke() {
    if (!apiKey) return;
    try {
      await revoke.mutateAsync(apiKey.id);
      onClose();
    } catch {
      /* error surfaced through the mutation state */
    }
  }

  return (
    <Dialog
      open={Boolean(apiKey)}
      onOpenChange={(open) => {
        if (!open) {
          revoke.reset();
          onClose();
        }
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Revoke this API key?</DialogTitle>
          <DialogDescription>
            Applications using this key will no longer authenticate. Revoking is immediate and
            cannot be undone.
          </DialogDescription>
        </DialogHeader>

        {apiKey ? (
          <p className="text-sm">
            <span className="font-medium">{apiKey.name}</span>{" "}
            <span className="font-mono text-xs text-muted-foreground">{apiKey.key_prefix}…</span>
          </p>
        ) : null}

        <InlineError error={revoke.error} />

        <DialogFooter>
          <Button variant="secondary" onClick={onClose} disabled={revoke.isPending}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleRevoke} disabled={revoke.isPending}>
            {revoke.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : null}
            Revoke key
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
