import { useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { ConsoleLayout } from "@/layouts/ConsoleLayout";
import { ApiKeysPage } from "@/pages/ApiKeysPage";
import { ApplicationsPage } from "@/pages/ApplicationsPage";
import { ConnectPage } from "@/pages/ConnectPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { ProjectDetailPage } from "@/pages/ProjectDetailPage";
import { ProjectsPage } from "@/pages/ProjectsPage";
import {
  ApiExplorerPage,
  BenchmarksPage,
  ComparePage,
  DocumentationPage,
  UsagePage,
} from "@/pages/placeholders";
import { useSession } from "@/hooks/useSession";
import { ApiError } from "@/lib/errors/apiError";
import { clearSession } from "@/lib/auth/session";

function handleAuthFailure(error: unknown) {
  // A rejected key invalidates the session immediately; the console then
  // returns to the connection screen instead of retrying with it.
  if (error instanceof ApiError && error.isAuthError) clearSession();
}

function createConsoleQueryClient(): QueryClient {
  return new QueryClient({
    queryCache: new QueryCache({ onError: handleAuthFailure }),
    mutationCache: new MutationCache({ onError: handleAuthFailure }),
    defaultOptions: {
      queries: {
        retry: (failureCount, error) => {
          if (error instanceof ApiError && error.status < 500 && error.status !== 0) return false;
          return failureCount < 2;
        },
        staleTime: 30_000,
        refetchOnWindowFocus: false,
      },
    },
  });
}

function ConsoleRoutes() {
  const { connected } = useSession();
  if (!connected) return <ConnectPage />;

  return (
    <Routes>
      <Route element={<ConsoleLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
        <Route path="/applications" element={<ApplicationsPage />} />
        <Route path="/api-keys" element={<ApiKeysPage />} />
        <Route path="/usage" element={<UsagePage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/benchmarks" element={<BenchmarksPage />} />
        <Route path="/api-explorer" element={<ApiExplorerPage />} />
        <Route path="/docs" element={<DocumentationPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  const [queryClient] = useState(createConsoleQueryClient);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ConsoleRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
