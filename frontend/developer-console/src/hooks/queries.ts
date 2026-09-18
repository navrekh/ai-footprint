import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  apiKeysApi,
  applicationsApi,
  benchmarksApi,
  compareApi,
  methodologyApi,
  organizationsApi,
  projectsApi,
  usageApi,
} from "@/lib/api/resources";
import { findConnectedApiKey } from "@/lib/auth/connectedKey";
import { getApiKey } from "@/lib/auth/session";
import { openApiApi } from "@/lib/api/openapi";
import { apiRequestWithMeta, type RequestOptions } from "@/lib/api/client";
import type {
  ApiKeyCreateRequest,
  ApplicationCreate,
  ApplicationUpdate,
  BenchmarkRunRequest,
  CompareRequest,
  ListParams,
  ProjectCreate,
  ProjectUpdate,
  UsageFilterParams,
} from "@/types/api";

export const queryKeys = {
  organization: (id: string) => ["organization", id] as const,
  projects: (limit: number) => ["projects", { limit }] as const,
  project: (id: string) => ["project", id] as const,
  applications: (project: string | null, limit: number) =>
    ["applications", { project, limit }] as const,
  application: (id: string) => ["application", id] as const,
  apiKeys: (limit: number) => ["api-keys", { limit }] as const,
  usageSummary: (filters: UsageFilterParams) => ["usage", "summary", filters] as const,
  usageByProvider: (filters: UsageFilterParams, paging: ListParams) =>
    ["usage", "by-provider", filters, paging] as const,
  usageByModel: (filters: UsageFilterParams, paging: ListParams) =>
    ["usage", "by-model", filters, paging] as const,
  usageByActivity: (filters: UsageFilterParams, paging: ListParams) =>
    ["usage", "by-activity", filters, paging] as const,
  usageByApplication: (filters: UsageFilterParams, paging: ListParams) =>
    ["usage", "by-application", filters, paging] as const,
  usageTimeseries: (filters: UsageFilterParams, granularity: string) =>
    ["usage", "timeseries", filters, granularity] as const,
  benchmarks: (activityType?: string, modality?: string) =>
    ["benchmarks", { activityType, modality }] as const,
  benchmark: (id: string) => ["benchmark", id] as const,
  methodology: ["methodology"] as const,
};

const LIST_LIMIT = 200;

export function useProjects(limit = LIST_LIMIT) {
  return useQuery({
    queryKey: queryKeys.projects(limit),
    queryFn: () => projectsApi.list({ limit }),
  });
}

export function useProject(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.project(projectId ?? ""),
    queryFn: () => projectsApi.get(projectId as string),
    enabled: Boolean(projectId),
  });
}

export function useOrganization(organizationId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.organization(organizationId ?? ""),
    queryFn: () => organizationsApi.get(organizationId as string),
    enabled: Boolean(organizationId),
  });
}

export function useApplications(project: string | null = null, limit = LIST_LIMIT) {
  return useQuery({
    queryKey: queryKeys.applications(project, limit),
    queryFn: () => applicationsApi.list({ project, limit }),
  });
}

export function useApiKeys(limit = LIST_LIMIT) {
  return useQuery({
    queryKey: queryKeys.apiKeys(limit),
    queryFn: () => apiKeysApi.list({ limit }),
  });
}

/**
 * Metadata of the API key this console is connected with, identified by
 * matching the session-held raw key against prefix metadata (see
 * src/lib/auth/connectedKey.ts for the documented API limitation). The raw
 * key itself is never exposed through this hook. `connected` is null when
 * the key cannot be identified uniquely — callers must treat that as
 * "unknown scope", never as a guessed scope.
 */
export function useConnectedApiKey() {
  const keys = useApiKeys();
  const rawKey = getApiKey();
  const connected = useMemo(
    () => findConnectedApiKey(rawKey, keys.data?.items),
    [rawKey, keys.data],
  );
  return { isPending: keys.isPending, error: keys.error, connected };
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProjectCreate) => projectsApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useUpdateProject(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProjectUpdate) => projectsApi.update(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: queryKeys.project(projectId) });
    },
  });
}

export function useCreateApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ApplicationCreate) => applicationsApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
  });
}

export function useUpdateApplication(applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ApplicationUpdate) => applicationsApi.update(applicationId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: queryKeys.application(applicationId) });
    },
  });
}

export function useCreateApiKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ApiKeyCreateRequest) => apiKeysApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["api-keys"] }),
  });
}

export function useRevokeApiKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (apiKeyId: string) => apiKeysApi.revoke(apiKeyId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["api-keys"] }),
  });
}

// ---------------------------------------------------------------------------
// Usage intelligence (GET /v1/usage/*) — derived from persisted workloads,
// never a client-side average or fabricated interpolation.
// ---------------------------------------------------------------------------

export function useUsageSummary(filters: UsageFilterParams) {
  return useQuery({
    queryKey: queryKeys.usageSummary(filters),
    queryFn: () => usageApi.summary(filters),
  });
}

export function useUsageByProvider(
  filters: UsageFilterParams,
  paging: ListParams = {},
  enabled = true,
) {
  return useQuery({
    queryKey: queryKeys.usageByProvider(filters, paging),
    queryFn: () => usageApi.byProvider(filters, paging),
    enabled,
  });
}

export function useUsageByModel(
  filters: UsageFilterParams,
  paging: ListParams = {},
  enabled = true,
) {
  return useQuery({
    queryKey: queryKeys.usageByModel(filters, paging),
    queryFn: () => usageApi.byModel(filters, paging),
    enabled,
  });
}

export function useUsageByActivity(
  filters: UsageFilterParams,
  paging: ListParams = {},
  enabled = true,
) {
  return useQuery({
    queryKey: queryKeys.usageByActivity(filters, paging),
    queryFn: () => usageApi.byActivity(filters, paging),
    enabled,
  });
}

export function useUsageByApplication(
  filters: UsageFilterParams,
  paging: ListParams = {},
  enabled = true,
) {
  return useQuery({
    queryKey: queryKeys.usageByApplication(filters, paging),
    queryFn: () => usageApi.byApplication(filters, paging),
    enabled,
  });
}

export function useUsageTimeseries(filters: UsageFilterParams, granularity: string) {
  return useQuery({
    queryKey: queryKeys.usageTimeseries(filters, granularity),
    queryFn: () => usageApi.timeseries(filters, granularity),
  });
}

// ---------------------------------------------------------------------------
// Compare (POST /v1/compare) — an on-demand action against a
// developer-supplied workload definition, not cached list data.
// ---------------------------------------------------------------------------

export function useCompare() {
  return useMutation({
    mutationFn: (payload: CompareRequest) => compareApi.create(payload),
  });
}

// ---------------------------------------------------------------------------
// Benchmarks (GET /v1/benchmarks, POST /v1/benchmarks/run) — public
// reference data plus an on-demand run action.
// ---------------------------------------------------------------------------

export function useBenchmarks(activityType?: string, modality?: string) {
  return useQuery({
    queryKey: queryKeys.benchmarks(activityType, modality),
    queryFn: () => benchmarksApi.list({ activity_type: activityType, modality }),
  });
}

export function useBenchmark(benchmarkId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.benchmark(benchmarkId ?? ""),
    queryFn: () => benchmarksApi.get(benchmarkId as string),
    enabled: Boolean(benchmarkId),
  });
}

export function useRunBenchmark() {
  return useMutation({
    mutationFn: (payload: BenchmarkRunRequest) => benchmarksApi.run(payload),
  });
}

// ---------------------------------------------------------------------------
// Methodology registry (GET /v1/methodology) — public, used to resolve a
// result's methodology_version into its assumptions/limitations/sources.
// ---------------------------------------------------------------------------

export function useMethodology() {
  return useQuery({
    queryKey: queryKeys.methodology,
    queryFn: () => methodologyApi.list(),
    staleTime: 5 * 60_000,
  });
}

// ---------------------------------------------------------------------------
// API Explorer — reuses the OpenAPI document the backend already generates
// (GET /openapi.json) to list endpoints, and the existing apiRequest
// client (via apiRequestWithMeta) to execute a request through the same
// authenticated session as every other page. No second API client, no new
// auth architecture.
// ---------------------------------------------------------------------------

export function useOpenApiSpec() {
  return useQuery({
    queryKey: ["openapi-spec"],
    queryFn: () => openApiApi.get(),
    staleTime: 5 * 60_000,
  });
}

export function useExecuteRequest() {
  return useMutation({
    mutationFn: (options: RequestOptions) => apiRequestWithMeta<unknown>(options),
  });
}
