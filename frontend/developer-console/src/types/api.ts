/**
 * Types mirroring the AI Footprint REST API contract
 * (backend/footprint-api/app/schemas). The backend is authoritative:
 * nothing here may add, rename, or reinterpret a field.
 */

export type ProjectStatus = "active" | "archived";
export type ApplicationStatus = "active" | "inactive";
export type ApplicationEnvironment = "development" | "staging" | "production";
export type ApiKeyStatus = "active" | "revoked";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string | null;
}

export interface ProjectUpdate {
  name?: string;
  description?: string | null;
  status?: ProjectStatus;
}

export interface Application {
  id: string;
  project_id: string;
  name: string;
  slug: string;
  description: string | null;
  status: string;
  environment: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationCreate {
  name: string;
  description?: string | null;
  environment?: ApplicationEnvironment | null;
  /** Required when authenticating with an organization-level API key. */
  project_id?: string | null;
}

export interface ApplicationUpdate {
  name?: string;
  description?: string | null;
  status?: ApplicationStatus;
  environment?: ApplicationEnvironment | null;
}

export interface ApiKey {
  id: string;
  organization_id: string;
  project_id: string | null;
  key_prefix: string;
  name: string;
  status: string;
  created_at: string;
  expires_at: string | null;
  last_used_at: string | null;
  revoked_at: string | null;
}

/** Raw key material — returned by the API exactly once, at creation time. */
export interface ApiKeyCreated {
  id: string;
  key: string;
  key_prefix: string;
  name: string;
}

export interface ApiKeyCreateRequest {
  name: string;
  project_id?: string | null;
  expires_at?: string | null;
}

export interface ListResponse<T> {
  items: T[];
  total: number;
}

export interface ListParams {
  limit?: number;
  offset?: number;
}
