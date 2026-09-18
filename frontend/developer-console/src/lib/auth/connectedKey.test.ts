import { describe, expect, it } from "vitest";

import { findConnectedApiKey, resolveConnectedKeyScope } from "@/lib/auth/connectedKey";
import type { ApiKey } from "@/types/api";

function makeKey(overrides: Partial<ApiKey>): ApiKey {
  return {
    id: "key_1",
    organization_id: "org_1",
    project_id: null,
    key_prefix: "afp_live_abc",
    name: "Console key",
    status: "active",
    created_at: "2026-01-01T00:00:00Z",
    expires_at: null,
    last_used_at: null,
    revoked_at: null,
    ...overrides,
  };
}

describe("findConnectedApiKey", () => {
  it("identifies an organization-level key by its public prefix metadata", () => {
    const key = makeKey({ project_id: null });
    const found = findConnectedApiKey("afp_live_abc-secret-material", [key]);
    expect(found?.organization_id).toBe("org_1");
    expect(found?.project_id).toBeNull();
  });

  it("identifies a project-scoped key", () => {
    const key = makeKey({ project_id: "proj_1" });
    const found = findConnectedApiKey("afp_live_abc-secret-material", [key]);
    expect(found?.project_id).toBe("proj_1");
  });

  it("returns null when no metadata row matches (scope stays unknown)", () => {
    expect(findConnectedApiKey("afp_live_zzz-secret", [makeKey({})])).toBeNull();
  });

  it("never guesses when the match is ambiguous", () => {
    const a = makeKey({ id: "key_1", key_prefix: "afp_live_abc" });
    const b = makeKey({ id: "key_2", key_prefix: "afp_live_abc" });
    expect(findConnectedApiKey("afp_live_abc-secret", [a, b])).toBeNull();
  });

  it("returns null without a raw key or metadata list", () => {
    expect(findConnectedApiKey(null, [makeKey({})])).toBeNull();
    expect(findConnectedApiKey("afp_live_abc-x", undefined)).toBeNull();
  });

  it("exposes only non-secret metadata — never raw key material", () => {
    const raw = "afp_live_abc-secret-material";
    const found = findConnectedApiKey(raw, [makeKey({})]);
    expect(found).not.toBeNull();
    const serialized = JSON.stringify(found);
    expect(serialized).not.toContain(raw);
    expect(Object.keys(found ?? {})).not.toContain("key");
  });
});

describe("resolveConnectedKeyScope", () => {
  it("maps project_id = null to an organization-level scope", () => {
    expect(resolveConnectedKeyScope(makeKey({ project_id: null }))).toEqual({
      kind: "organization",
    });
  });

  it("maps a project_id to a project scope carrying that id", () => {
    expect(resolveConnectedKeyScope(makeKey({ project_id: "proj_9" }))).toEqual({
      kind: "project",
      projectId: "proj_9",
    });
  });

  it("maps an unidentified key to unknown — never a guessed scope", () => {
    expect(resolveConnectedKeyScope(null)).toEqual({ kind: "unknown" });
  });
});
