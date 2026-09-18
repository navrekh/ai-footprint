/**
 * Identifying the connected credential (Sprint 5C review, fixes 1 & 2).
 *
 * KNOWN API LIMITATION: the AI Footprint API has no endpoint that returns
 * the authenticated key's own identity (no /v1/me or equivalent), and the
 * backend must not be changed to add one. The console therefore identifies
 * the connected key locally: the backend defines `key_prefix` as a leading
 * slice of the raw key, and GET /v1/api-keys returns that prefix plus
 * `organization_id` and `project_id` as non-secret metadata. Matching the
 * session-held raw key against those prefixes yields the connected key's
 * metadata without any new endpoint.
 *
 * Security invariants (ADR-012):
 * - the raw key is read from sessionStorage only and never leaves the tab —
 *   the comparison runs entirely in memory, nothing is sent, logged, or
 *   rendered;
 * - only the already-public metadata (id, organization_id, project_id,
 *   prefix, timestamps) is ever exposed to the UI;
 * - if the match is missing or ambiguous the console reports "unknown" and
 *   falls back to the safest UX — it never guesses a scope.
 */

import type { ApiKey } from "@/types/api";

/**
 * Returns the ApiKey metadata row for the connected raw key, or null when
 * the key cannot be identified uniquely (no match, or — defensively — more
 * than one match). Never returns or derives raw key material.
 */
export function findConnectedApiKey(
  rawKey: string | null,
  items: ApiKey[] | undefined,
): ApiKey | null {
  if (!rawKey || !items) return null;
  const matches = items.filter(
    (item) => item.key_prefix.length > 0 && rawKey.startsWith(item.key_prefix),
  );
  return matches.length === 1 ? matches[0] : null;
}

/**
 * The project scope of the connected credential, per the backend contract:
 * - organization-level key (project_id = null): may create organization-level
 *   keys, and must supply an explicit project_id to create a project-scoped key;
 * - project-scoped key (project_id set): restricted to its own project;
 * - unknown: the console could not identify the connected key — callers must
 *   use the safest contract-compatible UX (explicit project selection).
 */
export type ConnectedKeyScope =
  | { kind: "organization" }
  | { kind: "project"; projectId: string }
  | { kind: "unknown" };

export function resolveConnectedKeyScope(connected: ApiKey | null): ConnectedKeyScope {
  if (!connected) return { kind: "unknown" };
  if (connected.project_id) {
    return { kind: "project", projectId: connected.project_id };
  }
  return { kind: "organization" };
}
