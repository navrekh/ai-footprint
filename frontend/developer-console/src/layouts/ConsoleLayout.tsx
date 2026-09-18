import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  AppWindow,
  BarChart3,
  BookOpen,
  FolderKanban,
  Gauge,
  KeyRound,
  LayoutDashboard,
  LogOut,
  Menu,
  Scale,
  TerminalSquare,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { clearSession } from "@/lib/auth/session";
import { useSession } from "@/hooks/useSession";
import { cn } from "@/lib/utils/cn";

const NAV_SECTIONS = [
  {
    label: "Overview",
    items: [{ to: "/dashboard", label: "Dashboard", icon: LayoutDashboard }],
  },
  {
    label: "Organization",
    items: [
      { to: "/projects", label: "Projects", icon: FolderKanban },
      { to: "/applications", label: "Applications", icon: AppWindow },
      { to: "/api-keys", label: "API Keys", icon: KeyRound },
    ],
  },
  {
    label: "Resource intelligence",
    items: [
      { to: "/usage", label: "Usage", icon: BarChart3 },
      { to: "/compare", label: "Compare", icon: Scale },
      { to: "/benchmarks", label: "Benchmarks", icon: Gauge },
    ],
  },
  {
    label: "Developer",
    items: [
      { to: "/api-explorer", label: "API Explorer", icon: TerminalSquare },
      { to: "/docs", label: "Documentation", icon: BookOpen },
    ],
  },
] as const;

export function ConsoleLayout() {
  const { baseUrl } = useSession();
  const queryClient = useQueryClient();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  function handleDisconnect() {
    clearSession();
    queryClient.clear();
  }

  return (
    <div className="flex min-h-screen">
      <a
        href="#console-main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-surface focus:px-3 focus:py-2 focus:text-sm"
      >
        Skip to content
      </a>

      <aside
        id="console-sidebar"
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-border bg-surface transition-transform lg:static lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-14 items-center justify-between border-b border-border px-5">
          <div>
            <p className="text-sm font-semibold tracking-tight">AI Footprint</p>
            <p className="text-[11px] text-muted-foreground">Developer Console</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            aria-label="Close navigation"
            onClick={() => setMobileOpen(false)}
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>

        <nav aria-label="Console" className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
          {NAV_SECTIONS.map((section) => (
            <div key={section.label}>
              <p className="px-2 pb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                {section.label}
              </p>
              <ul className="space-y-0.5">
                {section.items.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      className={({ isActive }) =>
                        cn(
                          "flex items-center gap-2.5 rounded-[var(--radius-console)] px-2.5 py-2 text-sm transition-colors",
                          isActive
                            ? "bg-muted font-medium text-foreground"
                            : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
                        )
                      }
                    >
                      <item.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                      {item.label}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        <div className="border-t border-border px-4 py-4">
          <p className="truncate text-[11px] text-muted-foreground" title={baseUrl}>
            {baseUrl || "No API base URL"}
          </p>
          <Button
            variant="secondary"
            size="sm"
            className="mt-3 w-full"
            onClick={handleDisconnect}
          >
            <LogOut className="h-4 w-4" aria-hidden="true" />
            Disconnect
          </Button>
        </div>
      </aside>

      {mobileOpen ? (
        <div
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          aria-hidden="true"
          onClick={() => setMobileOpen(false)}
        />
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center gap-3 border-b border-border px-4 lg:hidden">
          <Button
            variant="ghost"
            size="icon"
            aria-label="Open navigation"
            aria-controls="console-sidebar"
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen(true)}
          >
            <Menu className="h-4 w-4" aria-hidden="true" />
          </Button>
          <span className="text-sm font-semibold">AI Footprint Console</span>
        </header>

        <main id="console-main" className="min-w-0 flex-1 px-4 py-6 sm:px-8 sm:py-8">
          <div className="mx-auto max-w-6xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
