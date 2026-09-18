import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiKeysApi, applicationsApi, organizationsApi, projectsApi } from "@/lib/api/resources";
import type {
  ApiKeyCreateRequest,
  ApplicationCreate,
  ApplicationUpdate,
  ProjectCreate,
  ProjectUpdate,
} from "@/types/api";

export const queryKeys = {
  organization: (id: string) => ["organization", id] as const,
  projects: (limit: number) => ["projects", { limit }] as const,
  project: (id: string) => ["project", id] as const,
  applications: (project: string | null, limit: number) =>
    ["applications", { project, limit }] as const,
  application: (id: string) => ["application", id] as const,
  apiKeys: (limit: number) => ["api-keys", { limit }] as const,
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
