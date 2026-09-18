import { apiRequest } from "@/lib/api/client";
import type {
  ApiKey,
  ApiKeyCreateRequest,
  ApiKeyCreated,
  Application,
  ApplicationCreate,
  ApplicationUpdate,
  ListParams,
  ListResponse,
  Organization,
  Project,
  ProjectCreate,
  ProjectUpdate,
} from "@/types/api";

const V1 = "/v1";

export const organizationsApi = {
  get: (organizationId: string) =>
    apiRequest<Organization>({ path: `${V1}/organizations/${organizationId}` }),
};

export const projectsApi = {
  list: (params: ListParams = {}) =>
    apiRequest<ListResponse<Project>>({
      path: `${V1}/projects`,
      query: { limit: params.limit ?? 50, offset: params.offset ?? 0 },
    }),
  get: (projectId: string) => apiRequest<Project>({ path: `${V1}/projects/${projectId}` }),
  create: (payload: ProjectCreate) =>
    apiRequest<Project>({ method: "POST", path: `${V1}/projects`, body: payload }),
  update: (projectId: string, payload: ProjectUpdate) =>
    apiRequest<Project>({ method: "PATCH", path: `${V1}/projects/${projectId}`, body: payload }),
};

export const applicationsApi = {
  list: (params: ListParams & { project?: string | null } = {}) =>
    apiRequest<ListResponse<Application>>({
      path: `${V1}/applications`,
      query: {
        project: params.project ?? undefined,
        limit: params.limit ?? 50,
        offset: params.offset ?? 0,
      },
    }),
  get: (applicationId: string) =>
    apiRequest<Application>({ path: `${V1}/applications/${applicationId}` }),
  create: (payload: ApplicationCreate) =>
    apiRequest<Application>({ method: "POST", path: `${V1}/applications`, body: payload }),
  update: (applicationId: string, payload: ApplicationUpdate) =>
    apiRequest<Application>({
      method: "PATCH",
      path: `${V1}/applications/${applicationId}`,
      body: payload,
    }),
};

export const apiKeysApi = {
  list: (params: ListParams = {}) =>
    apiRequest<ListResponse<ApiKey>>({
      path: `${V1}/api-keys`,
      query: { limit: params.limit ?? 50, offset: params.offset ?? 0 },
    }),
  /** The response contains raw key material — never persist or log it. */
  create: (payload: ApiKeyCreateRequest) =>
    apiRequest<ApiKeyCreated>({ method: "POST", path: `${V1}/api-keys`, body: payload }),
  revoke: (apiKeyId: string) =>
    apiRequest<ApiKey>({ method: "POST", path: `${V1}/api-keys/${apiKeyId}/revoke` }),
};

/**
 * Connection check. Uses a real authenticated endpoint — a successful
 * response is the only thing that marks the console as connected.
 */
export function verifyCredentials(baseUrl: string, apiKey: string) {
  return apiRequest<ListResponse<Project>>({
    path: `${V1}/projects`,
    query: { limit: 1, offset: 0 },
    credentials: { baseUrl, apiKey },
  });
}
