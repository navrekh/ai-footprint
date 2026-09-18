import { apiRequest } from "@/lib/api/client";
import type {
  ApiKey,
  ApiKeyCreateRequest,
  ApiKeyCreated,
  Application,
  ApplicationCreate,
  ApplicationUpdate,
  BenchmarkDefinition,
  BenchmarkListResponse,
  BenchmarkRunRequest,
  BenchmarkRunResponse,
  CompareRequest,
  CompareResponse,
  ListParams,
  ListResponse,
  Organization,
  Project,
  ProjectCreate,
  ProjectUpdate,
  UsageByActivityResponse,
  UsageByApplicationResponse,
  UsageByModelResponse,
  UsageByProviderResponse,
  UsageFilterParams,
  UsageSummary,
  UsageTimeseriesResponse,
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

function usageQuery(filters: UsageFilterParams, paging?: ListParams) {
  return {
    from: filters.from,
    to: filters.to,
    project: filters.project ?? undefined,
    application: filters.application ?? undefined,
    provider: filters.provider ?? undefined,
    model: filters.model ?? undefined,
    activity_type: filters.activity_type ?? undefined,
    ...(paging ? { limit: paging.limit ?? 50, offset: paging.offset ?? 0 } : {}),
  };
}

export const usageApi = {
  summary: (filters: UsageFilterParams = {}) =>
    apiRequest<UsageSummary>({ path: `${V1}/usage/summary`, query: usageQuery(filters) }),
  byProvider: (filters: UsageFilterParams = {}, paging: ListParams = {}) =>
    apiRequest<UsageByProviderResponse>({
      path: `${V1}/usage/by-provider`,
      query: usageQuery(filters, paging),
    }),
  byModel: (filters: UsageFilterParams = {}, paging: ListParams = {}) =>
    apiRequest<UsageByModelResponse>({
      path: `${V1}/usage/by-model`,
      query: usageQuery(filters, paging),
    }),
  byActivity: (filters: UsageFilterParams = {}, paging: ListParams = {}) =>
    apiRequest<UsageByActivityResponse>({
      path: `${V1}/usage/by-activity`,
      query: usageQuery(filters, paging),
    }),
  /** Does not accept an `application` filter — matches the backend contract. */
  byApplication: (filters: UsageFilterParams = {}, paging: ListParams = {}) =>
    apiRequest<UsageByApplicationResponse>({
      path: `${V1}/usage/by-application`,
      query: usageQuery({ ...filters, application: undefined }, paging),
    }),
  timeseries: (filters: UsageFilterParams = {}, granularity: string = "day") =>
    apiRequest<UsageTimeseriesResponse>({
      path: `${V1}/usage/timeseries`,
      query: { ...usageQuery(filters), granularity },
    }),
};

export const compareApi = {
  create: (payload: CompareRequest) =>
    apiRequest<CompareResponse>({ method: "POST", path: `${V1}/compare`, body: payload }),
};

export const benchmarksApi = {
  list: (params: { activity_type?: string; modality?: string } = {}) =>
    apiRequest<BenchmarkListResponse>({
      path: `${V1}/benchmarks`,
      query: { activity_type: params.activity_type, modality: params.modality },
    }),
  get: (benchmarkId: string) =>
    apiRequest<BenchmarkDefinition>({ path: `${V1}/benchmarks/${benchmarkId}` }),
  run: (payload: BenchmarkRunRequest) =>
    apiRequest<BenchmarkRunResponse>({
      method: "POST",
      path: `${V1}/benchmarks/run`,
      body: payload,
    }),
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
